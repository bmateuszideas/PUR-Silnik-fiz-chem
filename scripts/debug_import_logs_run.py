from pathlib import Path
import sqlite3
import json
from pur_mold_twin.cli.commands import import_logs
from pur_mold_twin.data.dataset import build_dataset

TMP = Path('tmp_debug_import')
if TMP.exists():
    import shutil
    shutil.rmtree(TMP)
TMP.mkdir()

db_path = TMP / 'logs.sqlite'
conn = sqlite3.connect(db_path)
try:
    conn.execute('''
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
    ''')
    conn.execute('''
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
    ''')
    conn.commit()
finally:
    conn.close()

# write datasource yaml
cfg = TMP / 'datasource.yaml'
cfg.write_text(f"""
driver: sqlite
dsn: \"{db_path}\"
table: process_logs
""",
               encoding='utf-8')

out = TMP / 'raw_logs'
# call import_logs (callable expects Path args)
import_logs(source_config=cfg, output_dir=out, system_id=None)

# inspect written qc.yaml
shot_dir = next(out.iterdir())
qc_file = shot_dir / 'qc.yaml'
print('QC YAML exists:', qc_file.exists())
print('QC YAML content:\n')
print(qc_file.read_text(encoding='utf-8'))

# load with ruamel shim
from ruamel.yaml import YAML
yaml = YAML(typ='safe')
with qc_file.open('r', encoding='utf-8') as fh:
    loaded = yaml.load(fh)
print('Loaded qc object:', loaded)
print('defects type:', type(loaded.get('defects')))
print('defects value:', loaded.get('defects'))

# build features
from pathlib import Path
sample_sim = Path('tests/data/ml/sample_sim_result.json')
features, _ = build_dataset(sample_sim, shot_dir, TMP / 'features.csv')
print('features any_defect:', features.iloc[0]['any_defect'])
