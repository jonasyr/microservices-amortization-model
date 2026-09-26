"""Ziehung der unsicheren Parameter (Beta-PERT, Standard λ = 4).

Die Parameter werden unabhängig voneinander gezogen (keine Korrelationen); die feste
Reihenfolge der Ziehung sorgt dafür, dass derselbe Seed dieselben Parametersätze liefert.
"""

import numpy as np

from .params import PERT_LAMBDA, UNCERTAIN


def pert(rng, low, mode, high, n, lam=PERT_LAMBDA):
    """Beta-PERT-Ziehung mit Formparameter lam."""
    if high == low:
        return np.full(n, float(mode))
    a = 1.0 + lam * (mode - low) / (high - low)
    b = 1.0 + lam * (high - mode) / (high - low)
    return low + rng.beta(a, b, size=n) * (high - low)


def sample(n, rng, fixed=None, lam=PERT_LAMBDA, dist="pert", ranges=None):
    """n Parameterziehungen als dict Symbol -> Array.

    fixed   Symbol -> fester Wert (überschreibt die Ziehung)
    lam     PERT-Formparameter (Robustheit: 2 bzw. 6)
    dist    "pert" oder "uniform" (Gleichverteilung auf [min, max])
    ranges  Symbol -> (min, Modus, max) als Ersatz für die Werte aus Tab. 2
    """
    fixed, ranges = fixed or {}, ranges or {}
    p = {}
    for u in UNCERTAIN:  # feste Reihenfolge -> reproduzierbar bei gleichem Seed
        low, mode, high = ranges.get(u.symbol, (u.low, u.mode, u.high))
        if dist == "uniform":
            draw = rng.uniform(low, high, size=n)
        else:
            draw = pert(rng, low, mode, high, n, lam=lam)
        p[u.symbol] = np.full(n, float(fixed[u.symbol])) if u.symbol in fixed else draw
    return p
