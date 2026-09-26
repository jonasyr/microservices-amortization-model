"""Auswertungsfunktionen: Kennzahlen, Schwellenwerte, partielle Rangkorrelation."""

import numpy as np
from scipy.stats import rankdata


def summary(a):
    """Median und 90-%-Intervall (5./95. Perzentil)."""
    q05, q50, q95 = np.percentile(a, [5, 50, 95])
    return {"median": float(q50), "q05": float(q05), "q95": float(q95), "mean": float(np.mean(a))}


def crossing(x, y, level):
    """Kleinstes x, an dem y die Schwelle `level` von unten erreicht (lineare Interpolation).

    Gibt None zurück, wenn die Schwelle im Bereich nicht erreicht wird.
    """
    x, y = np.asarray(x, float), np.asarray(y, float)
    if y[0] >= level:
        return float(x[0])
    idx = np.nonzero((y[:-1] < level) & (y[1:] >= level))[0]
    if idx.size == 0:
        return None
    j = idx[0]
    return float(x[j] + (level - y[j]) * (x[j + 1] - x[j]) / (y[j + 1] - y[j]))


def crossing_down(x, y, level):
    """Kleinstes x, an dem y die Schwelle `level` von oben unterschreitet."""
    return crossing(x, -np.asarray(y, float), -level)


def prcc(X, y):
    """Partielle Rangkorrelationskoeffizienten (PRCC) jeder Spalte von X mit y.

    Rangtransformation, dann Korrelation der Residuen aus linearen Regressionen von
    x_j bzw. y auf alle übrigen Spalten (Marino et al., 2008).
    """
    R = np.column_stack([rankdata(c) for c in X.T])
    ry = rankdata(y)
    n, k = R.shape
    out = np.empty(k)
    for j in range(k):
        Z = np.column_stack([np.ones(n), np.delete(R, j, axis=1)])
        bx, *_ = np.linalg.lstsq(Z, R[:, j], rcond=None)
        by, *_ = np.linalg.lstsq(Z, ry, rcond=None)
        ex, ey = R[:, j] - Z @ bx, ry - Z @ by
        out[j] = np.corrcoef(ex, ey)[0, 1]
    return out


def srrc(X, y):
    """Standardisierte Rangregressionskoeffizienten (SRRC) und R² der Rangregression.

    Bei unkorrelierten Eingaben entspricht SRRC² näherungsweise dem Anteil der Varianz der
    rangtransformierten Zielgröße, der auf den jeweiligen Parameter entfällt.
    """
    R = np.column_stack([rankdata(c) for c in X.T])
    ry = rankdata(y)
    Rz = (R - R.mean(axis=0)) / R.std(axis=0)
    yz = (ry - ry.mean()) / ry.std()
    beta, *_ = np.linalg.lstsq(Rz, yz, rcond=None)
    r2 = 1.0 - np.sum((yz - Rz @ beta) ** 2) / np.sum(yz ** 2)
    return beta, r2
