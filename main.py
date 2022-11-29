from enum import Enum

from fastapi import FastAPI
from pydantic import BaseModel

from history import HistoryEntry
from moex import MoexAPI
from spbex import SpbexAPI


class ErrorMessage(BaseModel):
    status: str
    description: str


class Exchange(str, Enum):
    Moex = "moex"
    Spbex = "spbex"


EXCHANGE_API_DICT = {
    Exchange.Moex: MoexAPI(),
    Exchange.Spbex: SpbexAPI(),
}


app = FastAPI()


@app.get("/{exchange}/{ticker}")
async def get_ticker(exchange: Exchange, ticker: str) -> list[HistoryEntry]:
    exchange = exchange.lower()
    ticker = ticker.lower()

    api = EXCHANGE_API_DICT.get(exchange, None)
    if api is None:
        return ErrorMessage(**{
            "status": "error",
            "description": "not implemented",
        })

    return await api.get_ticker(ticker)


@app.get("/healthcheck")
def healthcheck() -> ErrorMessage:
    return ErrorMessage(**{
        "status": "ok",
        "description": "healthy",
    })


@app.get("/")
def root_not_implemented() -> ErrorMessage:
    return ErrorMessage(**{
        "status": "error",
        "description": "not implemented",
    })
