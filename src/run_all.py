"""Führt alle Experimente aus und schreibt die Ergebnisse nach output/data/.

Aufruf (aus model/):  python -m src.run_all [--figures]
"""

import argparse
import json
import platform
import sys
import time
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd

from . import experiments as ex
from .params import (DISCOUNT_RATE, I_MONO, N0, N_RUNS, PERT_LAMBDA, SCENARIO_PROBS,
                     SCENARIOS, SEED, T_YEARS, UNCERTAIN)
from .sampling import sample

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "output" / "data"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--figures", action="store_true", help="Abbildungen erzeugen")
    args = ap.parse_args()
    DATA.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    rng = np.random.default_rng(SEED)
    p = sample(N_RUNS, rng)

    scen, d_ev = ex.scenarios(p)
    curve, thresholds = ex.growth_curve(p)
    be_summary, g_star, g_cap = ex.per_draw_breakeven(p)
    heat = ex.heatmap(p)
    prcc_table, h3 = ex.global_sensitivity(p, d_ev)
    torn = ex.tornado()
    hor = ex.horizon(p)
    prob_rows, prob_thr = ex.probability_sensitivity(p)
    disc = ex.discount_sensitivity(p)
    conv = ex.convergence(p, d_ev)
    trig = ex.trigger_shares(p)
    decomp = ex.trigger_decomposition(p)
    mono = ex.monotonicity(p)
    eq_rank = ex.equal_width_prcc()
    var = ex.variants()

    h1_share = scen["EV"]["anteil_MF_guenstiger"]
    h2_prob = scen["stark"]["P_MS_guenstiger"]
    hypotheses = {
        "H1": {"kriterium": f"Anteil EV(MF) < EV(MS) >= {ex.H1_MIN_SHARE}",
               "wert": h1_share, "ci": ex.mc_interval(h1_share, N_RUNS),
               "bestaetigt": bool(h1_share >= ex.H1_MIN_SHARE)},
        "H2": {"kriterium": f"P(MS günstiger | g = 60 %) > {ex.H2_MIN_PROB}",
               "wert": h2_prob, "ci": ex.mc_interval(h2_prob, N_RUNS),
               "bestaetigt": bool(h2_prob > ex.H2_MIN_PROB)},
        "H3": {"kriterium": "Rang(|PRCC|) von h und mu jeweils vor allen Betriebskostenparametern",
               "wert": {"schlechtester_rang_h_mu": h3["schlechtester_rang_A"],
                        "bester_rang_betrieb": h3["bester_rang_B"]},
               "bestaetigt": h3["bestaetigt"], "stark": h3["stark"],
               "r2_rangregression": h3["r2_rangregression"]},
    }

    results = {
        "meta": {
            "seed": SEED, "n_runs": N_RUNS, "pert_lambda": PERT_LAMBDA, "T": T_YEARS,
            "i": DISCOUNT_RATE, "N0": N0,
            "I_Mono": I_MONO, "szenarien": SCENARIOS, "wahrscheinlichkeiten": SCENARIO_PROBS,
            "pakete": {k: version(k) for k in ("numpy", "scipy", "pandas", "matplotlib")},
        },
        "parameter": [u.__dict__ for u in UNCERTAIN],
        "basisfall": ex.base_case_detail(),
        "szenarien": scen,
        "hypothesen": hypotheses,
        "breakeven": {"kurve_schwellen": thresholds, "je_ziehung": be_summary},
        "migration": {"anteile": trig, "zerlegung_stark": decomp},
        "sensitivitaet": {"prcc": prcc_table, "tornado": torn, "horizont": hor,
                          "p_stark": prob_thr, "zins": disc, "monotonie": mono,
                          "prcc_rang_gleiche_breite": eq_rank},
        "varianten": var,
        "konvergenz": conv,
    }
    # Umgebung und Laufzeit getrennt protokollieren: results.json und alle übrigen
    # Ergebnisdateien bleiben so über Rechner und Läufe hinweg byte-identisch (SHA256SUMS).
    run_log = {"python": sys.version.split()[0], "platform": platform.platform(),
               "laufzeit_s": round(time.time() - t0, 1)}

    (DATA / "results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False),
                                       encoding="utf-8")
    (DATA / "lauf.json").write_text(json.dumps(run_log, indent=2), encoding="utf-8")
    pd.DataFrame(curve).to_csv(DATA / "wachstumskurve.csv", index=False)
    pd.DataFrame(prob_rows).to_csv(DATA / "p_stark.csv", index=False)
    pd.DataFrame(hor).to_csv(DATA / "horizont.csv", index=False)
    pd.DataFrame(prcc_table).to_csv(DATA / "prcc.csv", index=False)
    pd.DataFrame(torn["zeilen"]).to_csv(DATA / "tornado.csv", index=False)
    pd.DataFrame(var).drop(columns=["H2_ci"]).to_csv(DATA / "varianten.csv", index=False)
    (DATA / "heatmap.json").write_text(json.dumps(heat), encoding="utf-8")
    np.savez_compressed(DATA / "breakeven_je_ziehung.npz", g_star=g_star, g_cap=g_cap)
    pd.DataFrame({k: v for k, v in p.items()}).assign(dEV=d_ev).to_csv(
        DATA / "ziehungen.csv.gz", index=False,
        compression={"method": "gzip", "mtime": 0})  # ohne Zeitstempel im gzip-Kopf

    print(f"fertig in {run_log['laufzeit_s']} s -> {DATA}")
    if args.figures:
        from .figures import make_all
        make_all(p)


if __name__ == "__main__":
    main()
