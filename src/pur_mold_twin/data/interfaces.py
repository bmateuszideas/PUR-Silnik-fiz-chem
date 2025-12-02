from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Optional

from .etl import LogBundle


@dataclass
class ProcessLogQuery:
    """
    Neutral query object for fetching process logs.

    Backends are free to ignore fields they do not support, but should keep
    the attribute names stable so CLI/configs remain portable.
    """

    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    mold_id: Optional[str] = None
    system_id: Optional[str] = None
    quality_status: Optional[str] = None
    limit: Optional[int] = None
    offset: int = 0


class ProcessLogSource:
    """
    Abstract source of process logs (SQL, files, APIs).

    Implementations are expected to return LogBundle objects compatible with
    existing ETL and feature-building helpers.
    """

    def fetch_shots(self, query: ProcessLogQuery) -> Iterable[LogBundle]:  # pragma: no cover - interface
        raise NotImplementedError

