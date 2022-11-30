import datetime

from pydantic import BaseModel


class HistoryEntry(BaseModel):
    date: datetime.date
    close: float | None
    high: float | None
    low: float | None
    volume: int | None
