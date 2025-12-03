from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd
import pytest
from typer.testing import CliRunner

from pur_mold_twin.cli.main import app
from pur_mold_twin.data.dataset import build_dataset


runner = CliRunner()


def _create_sqlite_with_sample_log(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE process_logs (
                shot_id TEXT PRIMARY KEY,
                system_id TEXT,
                m_polyol REAL,
                m_iso REAL,
                m_additives REAL,
                T_polyol_in_C REAL,
                T_iso_in_C REAL,
                T_mold_init_C REAL,
                T_ambient_C REAL,
                RH_ambient REAL,
                mixing_eff REAL,
                rho_moulded REAL,
                H_demold REAL,
                H_24h REAL,
                defect_risk_operator REAL,
                defects TEXT
            )
            """
        )
        conn.execute(
            """
            INSERT INTO process_logs (
                shot_id, system_id,
                m_polyol, m_iso, m_additives,
                T_polyol_in_C, T_iso_in_C, T_mold_init_C, T_ambient_C,
                RH_ambient, mixing_eff,
                rho_moulded, H_demold, H_24h,
                defect_risk_operator, defects
            ) VALUES (
                'SHOT_SQL_1', 'SYSTEM_R1',
                1.0, 1.05, 0.05,
                25.0, 25.0, 40.0, 22.0,
                0.55, 0.9,
                41.0, 43.0, 55.0,
                0.2, '["voids"]'
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def test_import_logs_and_build_features_e2e(tmp_path: Path) -> None:
    db_path = tmp_path / "logs.sqlite"
    _create_sqlite_with_sample_log(db_path)

    datasource_cfg = tmp_path / "datasource.yaml"
    datasource_cfg.write_text(
        f"""
driver: sqlite
dsn: "{db_path}"
table: process_logs
""",
        encoding="utf-8",
    )

    output_dir = tmp_path / "raw_logs"
    result = runner.invoke(
        app,
        [
            "import-logs",
            "--source",
            str(datasource_cfg),
            "--output-dir",
            str(output_dir),
        ],
    )
    assert result.exit_code == 0
    assert "Imported" in result.stdout

    # Build a minimal dataset by combining an existing simulation JSON
    # with the imported log directory.
    sample_sim = Path("tests/data/ml/sample_sim_result.json")
    shot_dir = next(output_dir.iterdir())
    features, _ = build_dataset(sample_sim, shot_dir, tmp_path / "features.csv")

    assert isinstance(features, pd.DataFrame)
    assert not features.empty
    row = features.iloc[0]
    # Assert that QC mapping from SQL ended up in the feature set
    assert row["qc_rho_moulded"] == pytest.approx(41.0)
    assert row["qc_H_demold"] == pytest.approx(43.0)
    assert row["qc_H_24h"] == pytest.approx(55.0)
    assert row["any_defect"] == 1

