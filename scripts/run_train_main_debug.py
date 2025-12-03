from pathlib import Path
import pandas as pd
from pur_mold_twin.ml.train_baseline import main

TMP = Path('tmp_debug_ml')
TMP.mkdir(exist_ok=True)
features = TMP / 'features.csv'
df = pd.DataFrame({
    'sim_T_core_max_C':[80.0,85.0],
    'sim_p_max_bar':[3.5,3.8],
    'defect_risk':[0.1,0.2],
    'any_defect':[0,1],
})
df.to_csv(features, index=False)

main(['--features', str(features), '--models-dir', str(TMP/'models'), '--metrics-path', str(TMP/'reports'/'ml'/'metrics.md')])
