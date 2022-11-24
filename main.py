from fastapi import FastAPI

from moex import MoexAPI
from spbex import SpbexAPI

app = FastAPI()

EXCHANGE_API_DICT = {
    "moex": MoexAPI(),
    "spbex": SpbexAPI(),
}


@app.get("/{exchange}/{ticker}")
async def get_ticker(exchange: str, ticker: str):
    exchange = exchange.lower()
    ticker = ticker.lower()

    api = EXCHANGE_API_DICT.get(exchange, None)
    if api is None:
        return {"error": "no api"}
    return await api.get_ticker(ticker)
