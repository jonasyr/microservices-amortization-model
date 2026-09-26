"""Plausibilitäts- und Extremwerttests des Kostenmodells."""

import numpy as np
import pytest

from src.analysis import crossing, prcc
from src.model import present_values
from src.params import I_MONO, UNCERTAIN, modes
from src.sampling import pert, sample


def base(**over):
    p = {k: np.array([v]) for k, v in modes().items()}
    p.update({k: np.array([v]) for k, v in over.items()})
    return p


def test_no_growth_no_migration_and_mono_cheaper():
    K_MS, K_MF, det = present_values(base(), 0.0, detail=True)
    assert np.isnan(det["migrationsstart_jahr"][0])
    assert det["MF"]["skalierung_migration"][0] == 0
    assert K_MF[0] < K_MS[0]


def test_identical_architectures_only_differ_by_investment():
    # ohne Mehraufwand, gleiche Exponenten, keine Migration: Differenz = 0
    p = base(kappa=0.0, omega=0.0, Phi=0.0, psi=0.0, gamma_S=0.6, gamma_M=0.6,
             beta_S=1.1, beta_M=1.1, s=0.0, h=1e9)
    K_MS, K_MF = present_values(p, 0.3)
    assert K_MS[0] == pytest.approx(K_MF[0], rel=1e-12)


def test_undiscounted_constant_costs_sum_correctly():
    p = base(gamma_M=0.0, beta_M=0.0, h=1e9)
    _, K_MF, det = present_values(p, 0.0, T=5, i=0.0, detail=True)
    W = modes()["w"] * I_MONO
    assert det["MF"]["wartung"][0] == pytest.approx(5 * W)
    assert det["MF"]["infrastruktur"][0] == pytest.approx(5 * (modes()["F_M"] + modes()["V"]))


def test_full_migration_cost_paid_when_completed_inside_horizon():
    # Kapazität sofort erreicht, Migration 1 Jahr, ohne Diskontierung: volle Kosten M
    p = base(h=1.0, d=1.0, mu=1.0)
    _, _, det = present_values(p, 0.5, T=5, i=0.0, detail=True)
    steps_after = det["MF"]["skalierung_migration"][0] - I_MONO
    assert steps_after >= 0
    assert steps_after < 5 * modes()["s"] + 1


def test_migration_truncated_at_horizon():
    # Migration beginnt spät -> nur anteilige Migrationskosten im Horizont
    p = base(h=5.0, d=3.0, mu=1.0)
    _, _, det = present_values(p, 0.6, T=5, i=0.0, detail=True)
    assert 0 < det["MF"]["skalierung_migration"][0] < I_MONO


def test_delta_increases_with_migration_cost():
    lo = present_values(base(mu=0.5), 0.8)
    hi = present_values(base(mu=2.0), 0.8)
    assert (hi[1] - hi[0])[0] > (lo[1] - lo[0])[0]


def test_vectorisation_matches_scalar_evaluation():
    rng = np.random.default_rng(1)
    p = sample(50, rng)
    K_MS, K_MF = present_values(p, 0.4)
    for j in (0, 17, 49):
        q = {k: np.array([v[j]]) for k, v in p.items()}
        a, b = present_values(q, 0.4)
        assert a[0] == pytest.approx(K_MS[j]) and b[0] == pytest.approx(K_MF[j])


def test_pert_respects_bounds_and_mode():
    rng = np.random.default_rng(0)
    for u in UNCERTAIN:
        x = pert(rng, u.low, u.mode, u.high, 20_000)
        assert x.min() >= u.low and x.max() <= u.high
        mean_expected = (u.low + 4 * u.mode + u.high) / 6
        assert x.mean() == pytest.approx(mean_expected, rel=0.02, abs=1e-3)


def test_crossing_interpolates():
    assert crossing([0, 1, 2], [0.0, 0.4, 0.8], 0.6) == pytest.approx(1.5)
    assert crossing([0, 1], [0.1, 0.2], 0.9) is None


def test_prcc_detects_monotone_dependence():
    rng = np.random.default_rng(3)
    X = rng.uniform(size=(2000, 3))
    y = 5 * X[:, 0] - 1 * X[:, 1] + rng.normal(scale=0.1, size=2000)
    r = prcc(X, y)
    assert r[0] > 0.9 and r[1] < -0.5 and abs(r[2]) < 0.1
