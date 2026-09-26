"""Experimente der Monte-Carlo-Analyse.

Alle Experimente nutzen dieselben Parameterziehungen (common random numbers), damit
Unterschiede zwischen Konfigurationen nicht auf Ziehungsrauschen zurückgehen.

Die Hypothesenkriterien wurden vor der Durchführung der Simulation im Forschungsplan festgelegt
(planning/chapter_plan.md, Abschnitt 3.3) und sind hier unverändert kodiert.

Modellvarianten (horizon, trigger) und Verteilungsvarianten dienen der Robustheitsprüfung;
der Basisfall ist horizon="cutoff", trigger="reactive", PERT mit λ = 4.
"""

import numpy as np

from .analysis import crossing, crossing_down, prcc, srrc, summary
from .model import CATEGORIES, delta, present_values
from .params import (DISCOUNT_RATE, N_RUNS, SCENARIO_PROBS, SCENARIOS, SEED, T_YEARS,
                     UNCERTAIN, UNCERTAIN_BY_SYMBOL, modes)
from .sampling import sample

# --- vorregistrierte Hypothesenkriterien ----------------------------------------
H1_MIN_SHARE = 0.80   # Anteil der Läufe mit EV(MF) < EV(MS)
H2_MIN_PROB = 0.50    # P(MS günstiger) im starken Szenario muss darüber liegen
H3_GROUP_A = ("h", "mu")                 # Kapazitätsreserve, Migrationskosten
H3_GROUP_B = ("w", "omega", "gamma_M", "gamma_S", "F_M", "Phi", "V", "psi",
              "beta_M", "beta_S", "s")   # laufende Betriebskosten

G_GRID = np.round(np.arange(0.0, 1.0001, 0.01), 4)
SYMBOLS = [u.symbol for u in UNCERTAIN]


def expected_delta(p, probs=SCENARIO_PROBS, T=T_YEARS, i=DISCOUNT_RATE, **model):
    """ΔEV = EV(MF) − EV(MS) je Ziehung (szenariogewichtete Kostendifferenz eines
    Parametersatzes); > 0 heißt Microservices im Erwartungswert über die Szenarien günstiger."""
    return sum(probs[s] * delta(p, g, T=T, i=i, **model) for s, g in SCENARIOS.items())


def mc_interval(share, n):
    """95-%-Intervall eines Anteils (Normalapproximation) und Standardfehler."""
    se = float(np.sqrt(share * (1 - share) / n))
    return {"se": se, "lo": max(0.0, share - 1.96 * se), "hi": min(1.0, share + 1.96 * se)}


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


def growth_curve(p, grid=G_GRID, T=T_YEARS, **model):
    """P(MS günstiger) und Verteilung von ΔK über die stetige Wachstumsachse."""
    rows = []
    for g in grid:
        dK = delta(p, g, T=T, **model)
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
    reverts = np.zeros(n, dtype=bool)          # nach erstem ΔK > 0 wieder ΔK ≤ 0
    for g in grid:
        pos = delta(p, g, T=T) > 0
        reverts |= ~np.isnan(g_star) & ~pos
        new = np.isnan(g_star) & pos
        g_star[new] = g
    g_cap = p["h"] ** (1.0 / T) - 1.0
    ok = ~np.isnan(g_star)
    from scipy.stats import spearmanr
    rho = spearmanr(g_star[ok], g_cap[ok]).statistic if ok.sum() > 2 else None
    diff = g_star[ok] - g_cap[ok]
    return {
        "anteil_mit_breakeven_bis_gmax": float(ok.mean()),
        "anteil_nicht_eindeutig": float(reverts.mean()),
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


def global_sensitivity(p, d_ev, n_boot=200, seed=SEED):
    """PRCC und Varianzanteile (SRRC²) aller Parameter mit ΔEV sowie mit ΔK im starken
    Szenario; Bootstrap-Intervalle der PRCC-Ränge; Prüfung von H3."""
    X = np.column_stack([p[s] for s in SYMBOLS])
    d_st = delta(p, SCENARIOS["stark"])
    r_ev, r_st = prcc(X, d_ev), prcc(X, d_st)
    s_ev, r2_ev = srrc(X, d_ev)
    s_st, r2_st = srrc(X, d_st)
    rng = np.random.default_rng(seed + 1)
    ranks = np.empty((n_boot, len(SYMBOLS)), dtype=int)
    n = X.shape[0]
    for b in range(n_boot):
        idx = rng.integers(0, n, n)
        rb = np.abs(prcc(X[idx], d_ev[idx]))
        ranks[b] = np.argsort(np.argsort(-rb)) + 1
    table = [{"symbol": s, "prcc_dEV": float(a), "prcc_dK_stark": float(b),
              "srrc2_dEV": float(c ** 2), "srrc2_dK_stark": float(e ** 2),
              "rang_boot_lo": int(np.percentile(ranks[:, j], 2.5)),
              "rang_boot_hi": int(np.percentile(ranks[:, j], 97.5))}
             for j, (s, a, b, c, e) in enumerate(zip(SYMBOLS, r_ev, r_st, s_ev, s_st))]
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
    h3["r2_rangregression"] = {"dEV": float(r2_ev), "dK_stark": float(r2_st)}
    return table, h3


def equal_width_prcc(n=N_RUNS, seed=SEED, rel=0.5):
    """PRCC-Ränge bei gleich breiten relativen Bereichen (Modus ± rel), um die Abhängigkeit
    der Rangfolge von den gesetzten Bereichsbreiten sichtbar zu machen."""
    ranges = {}
    for u in UNCERTAIN:
        if u.symbol == "psi":            # relative Größe um 0: V_S = V(1+ψ) ± rel
            ranges[u.symbol] = (-rel, 0.0, rel)
        else:
            ranges[u.symbol] = (u.mode * (1 - rel), u.mode, u.mode * (1 + rel))
    p = sample(n, np.random.default_rng(seed), ranges=ranges)
    X = np.column_stack([p[s] for s in SYMBOLS])
    r = np.abs(prcc(X, expected_delta(p)))
    order = np.argsort(-r)
    return {SYMBOLS[j]: k + 1 for k, j in enumerate(order)}


def monotonicity(p, symbols=("h", "d", "mu", "Phi", "kappa"), n_sub=2000, n_grid=9):
    """Anteil der Ziehungen, in denen ΔEV im jeweiligen Parameter monoton verläuft
    (Voraussetzung für die Deutung des PRCC)."""
    sub = {k: v[:n_sub] for k, v in p.items()}
    out = {}
    for sym in symbols:
        u = UNCERTAIN_BY_SYMBOL[sym]
        vals = np.linspace(u.low, u.high, n_grid)
        ys = np.column_stack([expected_delta(dict(sub, **{sym: np.full(n_sub, v)})) for v in vals])
        dif = np.diff(ys, axis=1)
        tol = 1e-6 * np.maximum(1.0, np.abs(ys).max(axis=1, keepdims=True))
        mono = np.all(dif >= -tol, axis=1) | np.all(dif <= tol, axis=1)
        out[sym] = float(mono.mean())
    return out


def trigger_shares(p, T=T_YEARS):
    """Anteil der Ziehungen mit ausgelöster bzw. im Horizont abgeschlossener Migration."""
    rows = {}
    for name, g in SCENARIOS.items():
        _, _, det = present_values(p, g, T=T, detail=True)
        start, end = det["migrationsstart_jahr"], det["migrationsende_jahr"]
        rows[name] = {"ausgeloest": float(np.mean(~np.isnan(start))),
                      "abgeschlossen": float(np.mean(end <= T))}
    return rows


def trigger_decomposition(p, g=SCENARIOS["stark"], T=T_YEARS):
    """P(MS günstiger | Migration ausgelöst / nicht ausgelöst) und Break-even ohne Grenze."""
    _, _, det = present_values(p, g, T=T, detail=True)
    trig = ~np.isnan(det["migrationsstart_jahr"])
    pos = delta(p, g, T=T) > 0
    no_limit = dict(p, h=np.full_like(p["h"], 1e9))
    _, thr = growth_curve(no_limit, grid=np.round(np.arange(0.0, 1.0001, 0.02), 4), T=T)
    return {"P_MS_ausgeloest": float(pos[trig].mean()) if trig.any() else None,
            "P_MS_nicht_ausgeloest": float(pos[~trig].mean()) if (~trig).any() else None,
            "g_bei_P50_ohne_grenze": thr["g_bei_P50"]}


VARIANTS = [
    # (Schlüssel, Beschreibung, Ziehungs-Optionen, Modell-Optionen, Zinssatz, Horizont)
    ("basis", "Basisfall (Tab. 2)", {}, {}, None, None),
    ("verpflichtung", "Beschlossene Migrationskosten voll angerechnet", {},
     {"horizon": "committed"}, None, None),
    ("vorausschauend", "Vorausschauende Migration", {}, {"trigger": "proactive"}, None, None),
    ("beides", "Voll angerechnet und vorausschauend", {},
     {"horizon": "committed", "trigger": "proactive"}, None, None),
    ("h_klein", "Kapazitätsreserve h: 2 / 4 / 10", {"ranges": {"h": (2.0, 4.0, 10.0)}}, {}, None, None),
    ("h_gross", "Kapazitätsreserve h: 2 / 10 / 50", {"ranges": {"h": (2.0, 10.0, 50.0)}}, {}, None, None),
    ("phi_niedrig", "Plattform-Grundlast niedrig (verwaltete Dienste): 5 / 15 / 30 Tsd.",
     {"ranges": {"Phi": (5_000, 15_000, 30_000)}}, {}, None, None),
    ("phi_hoch", "Plattform-Grundlast hoch (inkl. Betriebsstelle): 60 / 100 / 150 Tsd.",
     {"ranges": {"Phi": (60_000, 100_000, 150_000)}}, {}, None, None),
    ("skala5", "Skalenanker I_M × 5 (2 Mio. EUR)", {"I_M": 2_000_000}, {}, None, None),
    ("lambda2", "PERT λ = 2 (flacher)", {"lam": 2.0}, {}, None, None),
    ("lambda6", "PERT λ = 6 (spitzer)", {"lam": 6.0}, {}, None, None),
    ("gleich", "Gleichverteilung", {"dist": "uniform"}, {}, None, None),
    ("zins0", "Zinssatz 0 %", {}, {}, 0.0, None),
    ("zins10", "Zinssatz 10 %", {}, {}, 0.10, None),
    ("T10", "Horizont 10 Jahre", {}, {}, None, 10),
]


def variants(n=N_RUNS, seed=SEED, grid=np.round(np.arange(0.0, 1.0001, 0.02), 4)):
    """Robustheitsvarianten: H1-Anteil, P(MS | stark) mit 95-%-Intervall, g* (P = 50 %)
    und Übergangsbereich (P = 20 % bis 80 %)."""
    rows = []
    for key, label, samp, model, rate, T in VARIANTS:
        samp = dict(samp)
        I_M = samp.pop("I_M", None)
        p = sample(n, np.random.default_rng(seed), **samp)
        if I_M is not None:
            p["I_M"] = I_M
        i = DISCOUNT_RATE if rate is None else rate
        T = T_YEARS if T is None else T
        d_ev = expected_delta(p, T=T, i=i, **model)
        p_st = float(np.mean(delta(p, SCENARIOS["stark"], T=T, i=i, **model) > 0))
        curve = []
        for g in grid:
            curve.append(float(np.mean(delta(p, g, T=T, i=i, **model) > 0)))
        rows.append({
            "key": key, "label": label,
            "H1": float(np.mean(d_ev < 0)), "H2": p_st, "H2_ci": mc_interval(p_st, n),
            "mean_dEV": float(np.mean(d_ev)),
            "g_P20": crossing(grid, curve, 0.2), "g_P50": crossing(grid, curve, 0.5),
            "g_P80": crossing(grid, curve, 0.8),
        })
    return rows


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


def amortization_time(p, growth=(SCENARIOS["stark"], 1.0), T_max=10):
    """Amortisationsdauer je Ziehung: erster Monat, ab dem die bis dahin angefallene
    barwertige Kostendifferenz ΔK positiv ist (Microservices haben die Mehrinvestition
    eingespielt). Dient der Plausibilisierung gegen Praxisangaben zur Amortisationszeit."""
    months = np.arange(1, 12 * T_max + 1)
    out = {}
    for g in growth:
        t_am = np.full(len(p["h"]), np.nan)
        for m in months:
            new = np.isnan(t_am) & (delta(p, g, T=m / 12.0) > 0)
            t_am[new] = m / 12.0
        ok = ~np.isnan(t_am)
        out[f"{g:.2f}"] = {
            "g": float(g),
            **{f"anteil_bis_{y}_jahre": float(np.mean(t_am <= y)) for y in (2, 3, 5, T_max)},
            "dauer_amortisierender": summary(t_am[ok]) if ok.any() else None,
        }
    return out


def seed_stability(seeds=(SEED, 1, 42, 2026, 12345), n=N_RUNS):
    """Kernkennzahlen mit anderen Startwerten: H1-Anteil, P(MS günstiger | stark),
    Break-even-Wachstumsrate g* und einflussreichster Parameter nach |PRCC| mit ΔEV."""
    rows = []
    for s in seeds:
        q = sample(n, np.random.default_rng(s))
        scen, d_ev = scenarios(q)
        _, thr = growth_curve(q)
        r = np.abs(prcc(np.column_stack([q[k] for k in SYMBOLS]), d_ev))
        rows.append({"seed": int(s), "H1": scen["EV"]["anteil_MF_guenstiger"],
                     "H2": scen["stark"]["P_MS_guenstiger"], "g_P50": thr["g_bei_P50"],
                     "prcc_rang1": SYMBOLS[int(np.argmax(r))]})
    return rows
