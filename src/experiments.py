"""Experimente der Monte-Carlo-Analyse.

Alle Experimente nutzen dieselben Parameterziehungen (common random numbers), damit
Unterschiede zwischen Konfigurationen nicht auf Ziehungsrauschen zurückgehen.

Die Hypothesenkriterien sind vor dem ersten Simulationslauf festgelegt
(planning/chapter_plan.md, Abschnitt 3.3) und hier unverändert kodiert.
"""

import numpy as np

from .analysis import crossing, crossing_down, prcc, summary
from .model import CATEGORIES, delta, present_values
from .params import (DISCOUNT_RATE, SCENARIO_PROBS, SCENARIOS, T_YEARS, UNCERTAIN,
                     modes)

# --- vorregistrierte Hypothesenkriterien ----------------------------------------
H1_MIN_SHARE = 0.80   # Anteil der Läufe mit EV(MF) < EV(MS)
H2_MIN_PROB = 0.50    # P(MS günstiger) im starken Szenario muss darüber liegen
H3_GROUP_A = ("h", "mu")                 # Kapazitätsreserve, Migrationskosten
H3_GROUP_B = ("w", "omega", "gamma_M", "gamma_S", "F_M", "Phi", "V", "psi",
              "beta_M", "beta_S", "s")   # laufende Betriebskosten

G_GRID = np.round(np.arange(0.0, 1.0001, 0.01), 4)
SYMBOLS = [u.symbol for u in UNCERTAIN]


def expected_delta(p, probs=SCENARIO_PROBS, T=T_YEARS, i=DISCOUNT_RATE):
    """ΔEV = EV(MF) − EV(MS) je Ziehung; > 0 heißt Microservices im EV günstiger."""
    return sum(probs[s] * delta(p, g, T=T, i=i) for s, g in SCENARIOS.items())


def scenarios(p):
    """Gesamtkosten je Szenario, Erwartungswerte und Hypothesen H1/H2."""
    out, ev_ms, ev_mf = {}, 0.0, 0.0
    for name, g in SCENARIOS.items():
        K_MS, K_MF = present_values(p, g)
        dK = K_MF - K_MS
        out[name] = {
            "g": g, "p": SCENARIO_PROBS[name],
            "K_MS": summary(K_MS), "K_MF": summary(K_MF), "delta": summary(dK),
            "P_MS_guenstiger": float(np.mean(dK > 0)),
        }
        ev_ms = ev_ms + SCENARIO_PROBS[name] * K_MS
        ev_mf = ev_mf + SCENARIO_PROBS[name] * K_MF
    d_ev = ev_mf - ev_ms
    out["EV"] = {"EV_MS": summary(ev_ms), "EV_MF": summary(ev_mf), "delta": summary(d_ev),
                 "anteil_MF_guenstiger": float(np.mean(d_ev < 0))}
    return out, d_ev


def base_case_detail():
    """Kostenzerlegung je Kategorie im Basisfall (Modalwerte)."""
    p = {k: np.array([v]) for k, v in modes().items()}
    rows = {}
    for name, g in SCENARIOS.items():
        K_MS, K_MF, det = present_values(p, g, detail=True)
        rows[name] = {
            "MS": {c: float(det["MS"][c][0]) for c in CATEGORIES} | {"gesamt": float(K_MS[0])},
            "MF": {c: float(det["MF"][c][0]) for c in CATEGORIES} | {"gesamt": float(K_MF[0])},
            "migrationsstart_jahr": (None if np.isnan(det["migrationsstart_jahr"][0])
                                     else float(det["migrationsstart_jahr"][0])),
        }
    return rows


def growth_curve(p, grid=G_GRID, T=T_YEARS):
    """P(MS günstiger) und Verteilung von ΔK über die stetige Wachstumsachse."""
    rows = []
    for g in grid:
        dK = delta(p, g, T=T)
        rows.append({"g": float(g), "P_MS_guenstiger": float(np.mean(dK > 0)), **summary(dK)})
    P = [r["P_MS_guenstiger"] for r in rows]
    thresholds = {f"g_bei_P{int(l * 100)}": crossing(grid, P, l) for l in (0.2, 0.5, 0.8)}
    return rows, thresholds


def per_draw_breakeven(p, T=T_YEARS, g_max=1.5, step=0.005):
    """Break-even-Wachstumsrate je Ziehung (kleinstes g mit ΔK > 0) und Vergleich mit der
    Wachstumsrate, bei der die Kapazitätsgrenze genau am Horizontende erreicht wird."""
    grid = np.arange(0.0, g_max + 1e-9, step)
    n = len(p["h"])
    g_star = np.full(n, np.nan)
    for g in grid:
        pos = delta(p, g, T=T) > 0
        new = np.isnan(g_star) & pos
        g_star[new] = g
    g_cap = p["h"] ** (1.0 / T) - 1.0
    ok = ~np.isnan(g_star)
    from scipy.stats import spearmanr
    rho = spearmanr(g_star[ok], g_cap[ok]).statistic if ok.sum() > 2 else None
    diff = g_star[ok] - g_cap[ok]
    return {
        "anteil_mit_breakeven_bis_gmax": float(ok.mean()),
        "g_max": g_max,
        "g_star": summary(g_star[ok]),
        "g_kapazitaet": summary(g_cap),
        "spearman_gstar_gcap": None if rho is None else float(rho),
        "g_star_minus_g_cap": summary(diff),
    }, g_star, g_cap


def heatmap(p, g_grid=np.round(np.arange(0.0, 1.0001, 0.05), 3),
            h_grid=(2, 3, 4, 5, 6, 8, 10, 12, 15, 20), T=T_YEARS):
    """P(MS günstiger) über Wachstumsrate × Kapazitätsreserve (h fixiert, Rest zufällig)."""
    P = np.empty((len(h_grid), len(g_grid)))
    for a, h in enumerate(h_grid):
        q = dict(p, h=np.full_like(p["h"], float(h)))
        for b, g in enumerate(g_grid):
            P[a, b] = np.mean(delta(q, g, T=T) > 0)
    return {"g": [float(x) for x in g_grid], "h": [float(x) for x in h_grid],
            "P": P.round(4).tolist()}


def global_sensitivity(p, d_ev):
    """PRCC aller unsicheren Parameter mit ΔEV sowie mit ΔK im starken Szenario; H3."""
    X = np.column_stack([p[s] for s in SYMBOLS])
    r_ev = prcc(X, d_ev)
    r_st = prcc(X, delta(p, SCENARIOS["stark"]))
    table = [{"symbol": s, "prcc_dEV": float(a), "prcc_dK_stark": float(b)}
             for s, a, b in zip(SYMBOLS, r_ev, r_st)]
    table.sort(key=lambda r: -abs(r["prcc_dEV"]))
    rank = {r["symbol"]: k + 1 for k, r in enumerate(table)}
    worst_A = max(rank[s] for s in H3_GROUP_A)
    best_B = min(rank[s] for s in H3_GROUP_B)
    h3 = {"rang": rank, "schlechtester_rang_A": worst_A, "bester_rang_B": best_B,
          "bestaetigt": bool(worst_A < best_B)}
    # Zusatz: dieselbe Prüfung für ΔK im starken Szenario
    table_st = sorted(table, key=lambda r: -abs(r["prcc_dK_stark"]))
    rank_st = {r["symbol"]: k + 1 for k, r in enumerate(table_st)}
    h3["stark"] = {"rang": rank_st,
                   "bestaetigt": bool(max(rank_st[s] for s in H3_GROUP_A)
                                      < min(rank_st[s] for s in H3_GROUP_B))}
    return table, h3


def tornado(T=T_YEARS):
    """One-way-Variation jedes Parameters (min/max) um den Basisfall; Zielgröße ΔEV."""
    base = {k: np.array([v]) for k, v in modes().items()}
    ref = float(expected_delta(base, T=T)[0])
    rows = []
    for u in UNCERTAIN:
        lo = float(expected_delta(dict(base, **{u.symbol: np.array([u.low])}), T=T)[0])
        hi = float(expected_delta(dict(base, **{u.symbol: np.array([u.high])}), T=T)[0])
        rows.append({"symbol": u.symbol, "low": u.low, "high": u.high,
                     "dEV_low": lo, "dEV_high": hi, "spannweite": abs(hi - lo),
                     "vorzeichenwechsel": bool((lo > 0) != (ref > 0) or (hi > 0) != (ref > 0))})
    rows.sort(key=lambda r: -r["spannweite"])
    return {"dEV_basis": ref, "zeilen": rows}


def horizon(p, T_values=range(3, 11)):
    """Horizont-Sensitivität: H1-Anteil, P(MS günstiger) je Szenario, Break-even-g."""
    rows = []
    for T in T_values:
        d_ev = expected_delta(p, T=T)
        row = {"T": T, "anteil_MF_guenstiger_EV": float(np.mean(d_ev < 0))}
        for name, g in SCENARIOS.items():
            row[f"P_MS_{name}"] = float(np.mean(delta(p, g, T=T) > 0))
        _, thr = growth_curve(p, grid=np.round(np.arange(0.0, 1.0001, 0.02), 4), T=T)
        row["g_bei_P50"] = thr["g_bei_P50"]
        rows.append(row)
    return rows


def probability_sensitivity(p, steps=np.round(np.arange(0.0, 1.0001, 0.01), 3)):
    """Variation von p_stark bei konstantem Verhältnis p_niedrig : p_mittel = 3 : 5."""
    d = {s: delta(p, g) for s, g in SCENARIOS.items()}
    rho = SCENARIO_PROBS["niedrig"] / (SCENARIO_PROBS["niedrig"] + SCENARIO_PROBS["mittel"])
    rows = []
    for ps in steps:
        probs = {"niedrig": rho * (1 - ps), "mittel": (1 - rho) * (1 - ps), "stark": ps}
        d_ev = sum(probs[s] * d[s] for s in d)
        rows.append({"p_stark": float(ps), "anteil_MF_guenstiger": float(np.mean(d_ev < 0)),
                     "mean_dEV": float(np.mean(d_ev))})
    share = [r["anteil_MF_guenstiger"] for r in rows]
    return rows, {
        "p_stark_H1_kippt_unter_80": crossing_down(steps, share, H1_MIN_SHARE),
        "p_stark_MF_unter_50": crossing_down(steps, share, 0.5),
        "p_stark_mean_dEV_null": crossing(steps, [r["mean_dEV"] for r in rows], 0.0),
    }


def discount_sensitivity(p, rates=(0.0, 0.05, 0.10)):
    rows = []
    for i in rates:
        d_ev = expected_delta(p, i=i)
        rows.append({"i": i, "anteil_MF_guenstiger_EV": float(np.mean(d_ev < 0)),
                     "P_MS_stark": float(np.mean(delta(p, SCENARIOS["stark"], i=i) > 0))})
    return rows


def convergence(p, d_ev, checkpoints=(100, 250, 500, 1000, 2500, 5000, 10000)):
    d_st = delta(p, SCENARIOS["stark"])
    return [{"n": n, "anteil_MF_guenstiger_EV": float(np.mean(d_ev[:n] < 0)),
             "P_MS_stark": float(np.mean(d_st[:n] > 0))}
            for n in checkpoints if n <= len(d_ev)]
