import datetime
import json
import logging as log
import time

import httpx
from pydantic import BaseModel

from env import ENV
from history import HistoryEntry

if ENV.verbose:
    log.basicConfig()
    log.getLogger().setLevel(log.DEBUG)


class SpbexRange(BaseModel):
    start: int
    end: int


class SpbexAPI:

    base_url = "https://investcab.ru/api"

    async def get_ticker(self, ticker: str) -> list[HistoryEntry]:
        range = self.get_spbex_range()
        url = self.get_url_day_resolution(ticker, range)

        async with httpx.AsyncClient() as client:
            log.debug(f"Requesting security history for {ticker} via {url}")
            res = await client.get(url)

            if res.status_code != 200:
                log.fatal(f"{url} status code != 200")
                return []

            # not an error, it should be deserialized twice!
            j = res.json()
            j = json.loads(j)

        out = []
        for time, high, low, close in zip(j["t"], j["h"], j["l"], j["c"]):
            date = datetime.date.fromtimestamp(time)
            history_entry_dict = {
                "date": date,
                "close": close,
                "high": high,
                "low": low,
                "volume": 0.0,
            }
            history_entry = HistoryEntry(**history_entry_dict)
            out.append(history_entry)

        return out

    def get_spbex_range(self) -> SpbexRange:
        return SpbexRange(
            start=0,
            end=int(time.time()),
        )

    def get_url_day_resolution(self, ticker: str, range: SpbexRange) -> str:
        return self.get_url(ticker, "D", range)

    def get_url(self, ticker: str, resolution: str, range: SpbexRange) -> str:
        return f"{self.base_url}/chistory?symbol={ticker}&resolution={resolution}&from={range.start}&to={range.end}"
