import datetime
import logging as log

import httpx
import ujson
from pydantic import BaseModel

from dateutils import tomorrow_unix_moex
from env import ENV
from history import HistoryEntry
from redis_connection import redis_connection


class MoexSecurityParameters(BaseModel):
    board: str
    market: str
    engine: str


if ENV.verbose:
    log.basicConfig()
    log.getLogger().setLevel(log.DEBUG)


class Security:
    Date = 0
    Close = 1
    High = 2
    Low = 3
    Volume = 4
    Facevalue = 5


class Params:
    Board = 0
    Market = 1
    Engine = 2


class MoexAPI:
    base_url = "https://iss.moex.com"
    entries_per_page = 100
    is_primary_board = 1

    async def get_ticker(self, ticker: str) -> list[HistoryEntry]:
        security = await self._get_security_parameters(ticker)
        if security is None:
            log.fatal(f"No security parameters for {ticker}")
            return []

        out = []
        start = 0
        while True:
            entries = await self._get_security_history(ticker, security, start)
            out += entries
            start += self.entries_per_page
            if len(entries) != self.entries_per_page:
                break
        return out

    async def _fetch_security_history(self, url: str) -> str | None:
        async with httpx.AsyncClient() as client:
            res = await client.get(url)

            if res.status_code != 200:
                log.fatal(f"Get {url} status code != 200")
                return None

            return res.text

    async def _get_security_history(self, ticker: str, security: MoexSecurityParameters, start: int = 0) -> list[HistoryEntry]:
        url = self._get_security_history_url(ticker, security, start)

        if ENV.redis_enabled:
            log.debug(f"REDIS enabled, trying to get from cache {url}")
            cache = await redis_connection.get(url)
            if cache is not None:
                log.debug(f"Got cached result {cache}")
                j = ujson.loads(cache)
            else:
                log.debug(
                    f"No cached result, requesting security history for {ticker} via {url}")
                res = await self._fetch_security_history(url)
                j = ujson.loads(res)

                if len(j["history"]["data"]) == self.entries_per_page:
                    log.debug(
                        f"Saving {url} to cache forever because it has {self.entries_per_page} entries per page")
                    await redis_connection.set(url, res)
                else:
                    log.debug(
                        f"j['history']['data'] len is < {self.entries_per_page} so cache it until tomorrow")
                    await redis_connection.set(url, res, exat=tomorrow_unix_moex())
        else:
            log.debug(f"Requesting security history for {ticker} via {url}")
            res = await self._fetch_security_history(url)
            j = ujson.loads(res)

        if "history" not in j:
            log.debug("no history in j")
            return []

        if "columns" not in j["history"] or "data" not in j["history"]:
            log.debug("no columns or data in j['history']")
            return []

        is_bonds = "FACEVALUE" in j["history"]["columns"]

        out = []
        lower_ticker = ticker.lower()
        for entry in j["history"]["data"]:

            facevalue_coef = 1
            if is_bonds and entry[Security.Facevalue] is not None:
                facevalue_coef = entry[Security.Facevalue] / 100

            date = datetime.date.fromisoformat(entry[Security.Date])

            close = entry[Security.Close]
            if is_bonds and close is not None:
                close *= facevalue_coef

            high = entry[Security.High]
            if is_bonds and high is not None:
                high *= facevalue_coef

            low = entry[Security.Low]
            if is_bonds and low is not None:
                low *= facevalue_coef

            # in case of currency
            volume = 0
            if not "_tom" in lower_ticker:
                volume = entry[Security.Volume]

            history_entry_data = {
                "date": date,
                "close": close,
                "high": high,
                "low": low,
                "volume": volume,
            }
            history_entry = HistoryEntry(**history_entry_data)
            out.append(history_entry)

        return out

    def _get_security_history_url(self, ticker: str, security: MoexSecurityParameters, start) -> str:
        return f"{self.base_url}/iss/history/engines/{security.engine}/markets/{security.market}/boards/{security.board}/securities/{ticker}.json?iss.meta=off&start={start}&history.columns=TRADEDATE,CLOSE,HIGH,LOW,VOLUME,FACEVALUE"

    async def _get_security_parameters(self, ticker: str) -> MoexSecurityParameters | None:
        url = f"{self.base_url}/iss/securities/{ticker}.json?iss.only=boards&iss.meta=off&boards.columns=boardid,market,engine,is_primary"

        if ENV.redis_enabled:
            log.debug(f"REDIS enabled, trying to get from cache {url}")
            cache = await redis_connection.get(url)
            if cache is not None:
                log.debug(f"Got cached result {cache}")
                security_params = MoexSecurityParameters(**ujson.loads(cache))
                return security_params

        log.debug(f"REDIS disabled or no cached result for {url}")
        async with httpx.AsyncClient() as client:
            log.debug(f"Requesting security parameters for {ticker} via {url}")
            res = await client.get(url)

            if res.status_code != 200:
                log.fatal(f"{url} status code != 200")
                return None

            j = res.json()

            if "boards" not in j:
                log.fatal("boards not in response")
                return None

            if "data" not in j["boards"]:
                log.fatal("data not in j['boards']")
                return None

            if len(j["boards"]["data"]) < 1:
                log.fatal("j['boards']['data'] len < 1")
                return None

        for entry in j["boards"]["data"]:
            if entry[3] == self.is_primary_board:
                security_params_dict = {
                    "board": entry[Params.Board],
                    "market": entry[Params.Market],
                    "engine": entry[Params.Engine],
                }
                if ENV.redis_enabled:
                    log.debug(f"Saving {security_params_dict} to cache")
                    cached_json = ujson.dumps(security_params_dict)
                    await redis_connection.set(url, cached_json)
                return MoexSecurityParameters(**security_params_dict)

        log.fatal(f"Not found primary board for {ticker}")
        return None
