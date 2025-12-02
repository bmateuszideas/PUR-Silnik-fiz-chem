"""
Helper utilities for reaction kinetics used by the MVP 0D simulator.

Separating these helpers from ``mvp0d.py`` is the first step toward the
modular structure opisane w TODO2 §1 (wydzielenie logiki Arrheniusa oraz
kalibracji do osobnego pliku, ktory w przyszlosci wykorzysta zarowno
backend reczny jak i wariant `solve_ivp`).
"""

from __future__ import annotations

import math
from typing import List, Sequence, Tuple

from ..material_db.models import MaterialSystem


__all__ = [
    "ALPHA_STAGES",
    "arrhenius_multiplier",
    "calibrate_reaction_curve",
    "alpha_from_phi",
    "alpha_derivative",
]


ALPHA_STAGES: Sequence[Tuple[str, float]] = (
    ("cream_time_s", 0.05),
    ("gel_time_s", 0.35),
    ("rise_time_s", 0.75),
    ("tack_free_time_s", 0.92),
)

GAS_CONSTANT = 8.314462618  # J/(mol*K)


def arrhenius_multiplier(
    temperature_K: float,
    reference_temperature_K: float,
    activation_energy_J_per_mol: float,
) -> float:
    """Return Arrhenius scaling for given temperature."""

    temp = max(temperature_K, 250.0)
    reference = max(reference_temperature_K, 1e-6)
    exponent = (-activation_energy_J_per_mol / GAS_CONSTANT) * (
        (1.0 / temp) - (1.0 / reference)
    )
    return float(math.exp(exponent))


def alpha_from_phi(phi: float, exponent: float) -> float:
    phi_value = max(phi, 0.0)
    return float(1.0 - math.exp(-max(phi_value, 0.0) ** exponent))


def alpha_derivative(phi: float, exponent: float, dphi_dt: float) -> float:
    if dphi_dt <= 0.0 or phi <= 0.0:
        return 0.0
    phi_value = max(phi, 1e-12)
    exponent_term = exponent * (phi_value ** (exponent - 1.0))
    return math.exp(-phi_value ** exponent) * exponent_term * dphi_dt


def calibrate_reaction_curve(
    material: MaterialSystem,
    default_reaction_order: float,
) -> Tuple[float, float]:
    """Estimate tau/exponent pair from TDS cream/gel/rise/tack-free times."""

    pairs: List[Tuple[float, float]] = []
    polyol = material.polyol
    for field_name, alpha_target in ALPHA_STAGES:
        value = getattr(polyol, field_name, None)
        if value:
            pairs.append((float(value), alpha_target))

    if not pairs:
        return 120.0, max(default_reaction_order, 1.1)

    if len(pairs) == 1:
        t, alpha_target = pairs[0]
        tau = t / (-math.log(max(1e-6, 1 - alpha_target))) ** (
            1.0 / max(default_reaction_order, 1e-6)
        )
        return float(tau), max(default_reaction_order, 1.1)

    t1, a1 = pairs[0]
    t2, a2 = pairs[-1]
    A1 = -math.log(max(1e-6, 1 - a1))
    A2 = -math.log(max(1e-6, 1 - a2))
    if t1 == t2 or A1 == A2:
        return 120.0, max(default_reaction_order, 1.0)

    exponent = math.log(A1 / A2) / math.log(t1 / t2)
    exponent = float(max(0.8, min(exponent, 4.0)))
    tau = t1 / (A1 ** (1.0 / exponent))
    return float(tau), exponent
