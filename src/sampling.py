"""Ziehung der unsicheren Parameter aus Beta-PERT-Verteilungen."""

import numpy as np

from .params import UNCERTAIN


def pert(rng, low, mode, high, n, lam=4.0):
    """Beta-PERT-Ziehung mit Formparameter lam (Standard 4)."""
    if high == low:
        return np.full(n, float(mode))
    a = 1.0 + lam * (mode - low) / (high - low)
    b = 1.0 + lam * (high - mode) / (high - low)
    return low + rng.beta(a, b, size=n) * (high - low)


def sample(n, rng, fixed=None):
    """n Parameterziehungen als dict Symbol -> Array; `fixed` überschreibt einzelne Werte."""
    fixed = fixed or {}
    p = {}
    for u in UNCERTAIN:  # feste Reihenfolge -> reproduzierbar bei gleichem Seed
        draw = pert(rng, u.low, u.mode, u.high, n)
        p[u.symbol] = np.full(n, float(fixed[u.symbol])) if u.symbol in fixed else draw
    return p
