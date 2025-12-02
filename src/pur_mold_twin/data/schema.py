"""
Schema helpers for ML feature store.
"""

from __future__ import annotations

from typing import List


FEATURE_COLUMNS: List[str] = [
    "sim_T_core_max_C",
    "sim_T_core_t_at_max_s",
    "sim_p_max_bar",
    "sim_p_t_at_max_s",
    "sim_rho_moulded",
    "sim_t_demold_opt_s",
    "sim_defect_risk",
    "meas_T_core_max_C",
    "meas_T_core_t_at_max_s",
    "meas_T_core_avg_0_120_C",
    "meas_T_core_slope_0_60_C_per_s",
    "meas_p_max_bar",
    "meas_p_t_at_max_s",
    "meas_p_slope_0_60_bar_per_s",
    "delta_T_core_max_C",
    "delta_p_max_bar",
    "delta_t_demold_s",
    "qc_rho_moulded",
    "qc_H_demold",
    "qc_H_24h",
    "proc_T_polyol_in_C",
    "proc_T_iso_in_C",
    "proc_T_mold_init_C",
    "proc_RH_ambient",
    "proc_mixing_eff",
]

TARGET_COLUMNS: List[str] = [
    "defect_risk",
    "any_defect",
]
