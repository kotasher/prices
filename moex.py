import datetime
import json
import logging as log
from dataclasses import dataclass

import httpx

from dateutil import tomorrow_unix
from env import ENV
from history import HistoryEntry
from redis_connection import redis_connection


@dataclass
class MoexSecurityParameters:
    board: str = ""
    market: str = ""
    engine: str = ""


if ENV.verbose:
    log.basicConfig()
    log.getLogger().setLevel(log.DEBUG)


class MoexAPI:
    base_url = "https://iss.moex.com"

    async def get_ticker(self, ticker: str) -> list[HistoryEntry]:
        security = await self._get_security_parameters(ticker)
        if security is None:
            log.fatal(f"No security parameters for {ticker}")
            return []

        out = []
        start = 0
        while True:
            entries = await self._get_security_history(ticker, security, start)
            if len(entries) == 0:
                break
            out += entries
            start += 100

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
            cache = redis_connection.get(url)
            if cache is not None:
                log.debug(f"Got cached result {cache}")
                j = json.loads(cache)
            else:
                log.debug(
                    f"No cached result, requesting security history for {ticker} via {url}")
                res = await self._fetch_security_history(url)
                j = json.loads(res)

                if len(j["history"]["data"]) != 0:
                    log.debug(f"Saving {url} to cache for 1 hour")
                    redis_connection.set(url, json.dumps(j), exat=tomorrow_unix())
                else:
                    log.debug("j['history']['data'] len is = 0")

        else:
            log.debug(f"Requesting security history for {ticker} via {url}")
            res = await self._fetch_security_history(url)
            j = json.loads(res)

        if "history" not in j:
            log.debug("no history in j")
            return []

        if "data" not in j["history"]:
            log.debug("no data in j['history']")
            return []

        out = []
        for entry in j["history"]["data"]:

            date = datetime.date.fromisoformat(entry[0])
            close = entry[1]
            high = entry[2]
            low = entry[2]
            volume = entry[3]

            # bonds
            if len(entry) == 6:
                facevalue_coef = entry[5] / 100
                close *= facevalue_coef
                high *= facevalue_coef
                low *= facevalue_coef

            history_entry = HistoryEntry(date, close, high, low, volume)
            out.append(history_entry)

        return out

    def _get_security_history_url(self, ticker: str, security: MoexSecurityParameters, start) -> str:
        return f"{self.base_url}/iss/history/engines/{security.engine}/markets/{security.market}/boards/{security.board}/securities/{ticker}.json?iss.meta=off&start={start}&history.columns=TRADEDATE,CLOSE,HIGH,LOW,VOLUME,FACEVALUE"

    async def _get_security_parameters(self, ticker: str) -> MoexSecurityParameters | None:
        url = f"{self.base_url}/iss/securities/{ticker}.json?iss.only=boards&iss.meta=off&boards.columns=boardid,market,engine,is_primary"

        if ENV.redis_enabled:
            log.debug(f"REDIS enabled, trying to get from cache {url}")
            cache = redis_connection.get(url)
            if cache is not None:
                log.debug(f"Got cached result {cache}")
                security_params = MoexSecurityParameters()
                security_params.__dict__ = json.loads(cache)
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
            if entry[3] == 1:
                security_params = MoexSecurityParameters(
                    entry[0], entry[1], entry[2])
                if ENV.redis_enabled:
                    log.debug(f"Saving {security_params.__dict__} to cache")
                    cached_json = json.dumps(security_params.__dict__)
                    redis_connection.set(url, cached_json)
                return security_params

        log.fatal(f"Not found primary board for {ticker}")
        return None
