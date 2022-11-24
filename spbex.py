import datetime
import json
import logging as log
import time
from dataclasses import dataclass

import requests

from history import HistoryEntry

# log.basicConfig()
# log.getLogger().setLevel(log.DEBUG)


@dataclass
class SpbexRange:
    start: int
    end: int


class SpbexAPI:

    base_url = "https://investcab.ru/api"

    def get_ticker(self, ticker: str) -> list[HistoryEntry]:
        range = self.get_spbex_range()
        url = self.get_url_day_resolution(ticker, range)
        log.debug(f"Requesting security history for {ticker} via {url}")
        res = requests.get(url)

        if res.status_code != 200:
            log.fatal(f"{url} status code != 200")
            return []

        j = res.json()
        j = json.loads(j)

        out = []
        for time, high, low, close in zip(j["t"], j["h"], j["l"], j["c"]):
            date = datetime.date.fromtimestamp(time)
            history_entry = HistoryEntry(date, close, high, low, 0.0)
            out.append(history_entry)

        return out

    def get_spbex_range(self) -> SpbexRange:
        return SpbexRange(
            start=1434014660,
            end=int(time.time()),
        )

    def get_url_day_resolution(self, ticker: str, range: SpbexRange) -> str:
        return self.get_url(ticker, "D", range)

    def get_url(self, ticker: str, resolution: str, range: SpbexRange) -> str:
        return f"{self.base_url}/chistory?symbol={ticker}&resolution={resolution}&from={range.start}&to={range.end}"
