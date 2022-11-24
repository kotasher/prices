import datetime
from dataclasses import dataclass


@dataclass
class HistoryEntry:
    date: datetime.date
    close: float
    high: float
    low: float
    volume: float
