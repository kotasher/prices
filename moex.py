import datetime
import logging as log
from dataclasses import dataclass

import requests

from history import HistoryEntry


@dataclass
class MoexSecurityParameters:
    board: str
    market: str
    engine: str


# log.basicConfig()
# log.getLogger().setLevel(log.DEBUG)


class MoexAPI:
    base_url = "https://iss.moex.com"

    def get_ticker(self, ticker: str) -> list[HistoryEntry]:
        security = self.get_security_parameters(ticker)
        if security is None:
            log.fatal(f"No security parameters for {ticker}")
            return []

        out = []
        start = 0
        while True:
            entries = self.get_security_history(ticker, security, start)
            if len(entries) == 0:
                break
            out += entries
            start += 100

        return out

    def get_security_history(self, ticker: str, security: MoexSecurityParameters, start: int = 0) -> list[HistoryEntry]:
        url = self.get_security_history_url(ticker, security, start)
        log.debug(f"Requesting security history for {ticker} via {url}")
        res = requests.get(url)

        if res.status_code != 200:
            log.fatal(f"Get {url} status code != 200")
            return []

        j = res.json()

        if "history" not in j:
            log.fatal("history not in j")
            return []

        if "data" not in j["history"]:
            log.fatal("data not in j['history']")
            return []

        if len(j["history"]["data"]) < 1:
            log.debug("j['history']['data'] len is 0")
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

    def get_security_history_url(self, ticker: str, security: MoexSecurityParameters, start) -> str:
        return f"{self.base_url}/iss/history/engines/{security.engine}/markets/{security.market}/boards/{security.board}/securities/{ticker}.json?iss.meta=off&start={start}&history.columns=TRADEDATE,CLOSE,HIGH,LOW,VOLUME,FACEVALUE"

    def get_security_parameters(self, ticker: str) -> MoexSecurityParameters | None:
        url = f"{self.base_url}/iss/securities/{ticker}.json?iss.only=boards&iss.meta=off&boards.columns=boardid,market,engine,is_primary"
        log.debug(f"Requesting security parameters for {ticker} via {url}")
        res = requests.get(url)

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
                return MoexSecurityParameters(entry[0], entry[1], entry[2])

        log.fatal(f"Not found primary board for {ticker}")
        return None
