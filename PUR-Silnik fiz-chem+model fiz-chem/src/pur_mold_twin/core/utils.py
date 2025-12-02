from __future__ import annotations

from typing import Iterable, List, Sequence

GAS_CONSTANT = 8.314462618  # J/(mol*K)
MOLAR_MASS_WATER = 0.01801528  # kg/mol
MOLAR_MASS_PENTANE = 0.07215  # kg/mol
STANDARD_PRESSURE_PA = 101_325.0
LIQUID_WATER_DENSITY_KG_PER_M3 = 1_000.0


def linspace(start: float, stop: float, steps: int) -> List[float]:
    if steps <= 1:
        return [float(stop)]
    delta = (stop - start) / (steps - 1)
    return [start + i * delta for i in range(steps)]


def zeros_like(sequence: Sequence[object]) -> List[float]:
    return [0.0 for _ in sequence]


def ones_like(sequence: Sequence[object]) -> List[float]:
    return [1.0 for _ in sequence]


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def celsius_to_kelvin(value: float) -> float:
    return value + 273.15


def interp_series(time: Sequence[float], values: Sequence[float], target: float) -> float:
    """Linear interpolation similar to numpy.interp (time assumed sorted)."""

    if not time:
        return float(values[-1] if values else 0.0)
    if target <= time[0]:
        return float(values[0])
    if target >= time[-1]:
        return float(values[-1])
    for idx in range(1, len(time)):
        if target <= time[idx]:
            t0, t1 = time[idx - 1], time[idx]
            v0, v1 = values[idx - 1], values[idx]
            span = t1 - t0 or 1e-9
            fraction = (target - t0) / span
            return float(v0 + fraction * (v1 - v0))
    return float(values[-1])
