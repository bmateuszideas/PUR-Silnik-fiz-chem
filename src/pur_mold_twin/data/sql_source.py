from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd
from ruamel.yaml import YAML

from .etl import LogBundle
from .interfaces import ProcessLogQuery, ProcessLogSource


@dataclass
class SQLSourceConfig:
    """Configuration for SQL-based log source."""

    driver: str
    dsn: str
    table: str


class SQLProcessLogSource(ProcessLogSource):
    """
    Simple SQL-backed ProcessLogSource.

    Current implementation focuses on SQLite for tests and local development.
    Other drivers can reuse the same contract by providing a DB-API compatible
    connection for the configured DSN.
    """

    def __init__(self, config: SQLSourceConfig) -> None:
        self.config = config

    def _connect(self):
        if self.config.driver == "sqlite":
            return sqlite3.connect(self.config.dsn)
        raise RuntimeError(f"Unsupported SQL driver '{self.config.driver}'")

    def fetch_shots(self, query: ProcessLogQuery) -> Iterable[LogBundle]:
        conn = self._connect()
        try:
            conn.row_factory = sqlite3.Row
            sql = f"SELECT * FROM {self.config.table}"
            params: list = []
            # Basic filters (start_time/end_time/system_id) are optional; for now we only
            # support system_id as an example.
            where_clauses = []
            if query.system_id:
                where_clauses.append("system_id = ?")
                params.append(query.system_id)
            if where_clauses:
                sql += " WHERE " + " AND ".join(where_clauses)
            if query.limit is not None:
                sql += " LIMIT ? OFFSET ?"
                params.extend([query.limit, query.offset])

            cursor = conn.execute(sql, params)
            for row in cursor.fetchall():
                yield self._row_to_bundle(row)
        finally:
            conn.close()

    def _row_to_bundle(self, row: sqlite3.Row) -> LogBundle:
        process = {
            "m_polyol": row["m_polyol"],
            "m_iso": row["m_iso"],
            "m_additives": row["m_additives"],
            "T_polyol_in_C": row["T_polyol_in_C"],
            "T_iso_in_C": row["T_iso_in_C"],
            "T_mold_init_C": row["T_mold_init_C"],
            "T_ambient_C": row["T_ambient_C"],
            "RH_ambient": row["RH_ambient"],
            "mixing_eff": row["mixing_eff"],
        }
        qc = {
            "rho_moulded": row["rho_moulded"],
            "H_demold": row["H_demold"],
            "H_24h": row["H_24h"],
            "defect_risk_operator": row["defect_risk_operator"],
            "defects": json.loads(row["defects"]) if row["defects"] else [],
        }
        metadata = {
            "shot_id": row["shot_id"],
            "system_id": row["system_id"],
        }
        measured = pd.DataFrame()  # timeseries can be added in future iterations
        return LogBundle(process=process, measured=measured, qc=qc, metadata=metadata)


def load_sql_source_from_yaml(path: Path) -> SQLProcessLogSource:
    yaml = YAML(typ="safe")
    data = yaml.load(path.read_text(encoding="utf-8")) or {}
    driver = data.get("driver", "sqlite")
    dsn = str(data.get("dsn") or data.get("database") or "")
    table = data.get("table", "process_logs")
    if not dsn:
        raise ValueError(f"Missing DSN/database in SQL source config '{path}'")
    config = SQLSourceConfig(driver=driver, dsn=dsn, table=table)
    return SQLProcessLogSource(config)

