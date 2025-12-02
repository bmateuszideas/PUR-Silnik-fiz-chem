from __future__ import annotations

from typing import List, Optional, Sequence

from .utils import clamp, interp_series


def compute_hardness_profile(alpha: Sequence[float], rho: Sequence[float], config) -> List[float]:
    density_ref = max(config.hardness_density_ref, 1.0)
    values: List[float] = []
    for alpha_value, rho_value in zip(alpha, rho):
        density_term = max(rho_value - density_ref, 0.0) / density_ref
        values.append(
            config.hardness_base_shore
            + config.hardness_alpha_gain * alpha_value
            + config.hardness_density_gain * density_term
        )
    return values


def predict_h24(rho_moulded: float, config) -> float:
    density_ref = max(config.hardness_density_ref, 1.0)
    density_term = max(rho_moulded - density_ref, 0.0) / density_ref
    return (
        config.hardness_base_shore
        + config.hardness_alpha_gain
        + config.hardness_density_gain * density_term
        + config.hardness_24h_bonus
    )


def demold_window(
    time: Sequence[float],
    alpha: Sequence[float],
    rho: Sequence[float],
    T_core: Sequence[float],
    hardness_profile: Sequence[float],
    quality,
) -> tuple[Optional[float], Optional[float], Optional[float]]:
    indices = []
    for idx in range(len(time)):
        if (
            alpha[idx] >= quality.alpha_demold_min
            and quality.rho_moulded_min <= rho[idx] <= quality.rho_moulded_max
            and (T_core[idx] - 273.15) <= quality.core_temp_max_C
            and hardness_profile[idx] >= quality.H_demold_min_shore
        ):
            indices.append(idx)
    if not indices:
        return None, None, None

    t_min = float(time[indices[0]])
    t_max = float(time[indices[-1]])
    t_opt = t_min + 0.3 * (t_max - t_min)
    return t_min, t_max, t_opt


def sample_profile(time: Sequence[float], values: Sequence[float], time_target: Optional[float]) -> float:
    if time_target is None:
        return float(values[-1])
    return float(interp_series(time, values, time_target))
