"""Erzeugt LaTeX-Tabellen und Zahlen-Makros aus output/data/results.json.

Jede Zahl im Fließtext wird über ein Makro aus tabellen/zahlen.tex gesetzt, damit Text,
Tabellen und Abbildungen dieselbe Quelle haben. Belege und Herkunft der Parameter kommen
ausschließlich aus params.py.
Aufruf (aus model/):  python -m src.tables
"""

import json
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from .analysis import crossing
from .params import I_MONO, N0, N_RUNS, PERT_LAMBDA, SEED, UNCERTAIN

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "output" / "data"
# Innerhalb der Projektarbeit landen die Tabellen im LaTeX-Projekt, eigenständig unter output/
IN_PAPER = (ROOT.parent / "main.tex").exists()
TAB = ROOT.parent / "tabellen" if IN_PAPER else ROOT / "output" / "tabellen"

ORIGIN = {"hergeleitet": "H", "relation_belegt": "R", "gesetzt": "G"}
SYMBOL_TEX = {
    "kappa": r"\kappa", "w": "w", "omega": r"\omega", "gamma_M": r"\gamma_{\mathrm{M}}",
    "gamma_S": r"\gamma_{\mathrm{S}}", "F_M": r"F_{\mathrm{M}}", "Phi": r"\Phi", "V": "V",
    "psi": r"\psi", "beta_M": r"\beta_{\mathrm{M}}", "beta_S": r"\beta_{\mathrm{S}}",
    "s": "s", "h": "h", "mu": r"\mu", "d": "d",
}
SHORT_NAME = {
    "kappa": r"Mehraufwand Erstentwicklung MS (Anteil an $I_{\mathrm{M}}$)",
    "w": r"Wartung p.\,a. bei $N_0$ (Anteil an $I_{\mathrm{M}}$)",
    "omega": "Entwicklungs- und Wartungsmehraufwand MS",
    "gamma_M": "Wartungsexponent Monolith",
    "gamma_S": "Wartungsexponent MS",
    "F_M": "Infrastruktur-Fixkosten Monolith (EUR/a)",
    "Phi": "Plattform-Grundlast MS (EUR/a)",
    "V": r"lastabhängige Infrastruktur bei $N_0$ (EUR/a)",
    "psi": "Abweichung lastabhängiger Infrastrukturkosten MS",
    "beta_M": "Infrastrukturexponent Monolith",
    "beta_S": "Infrastrukturexponent MS",
    "s": "Kapazitätsstufe MS je Verdopplung (EUR)",
    "h": r"Kapazitätsreserve Monolith ($N_{\mathrm{krit}}/N_0$)",
    "mu": r"Migrationskosten (Vielfaches von $I_{\mathrm{M}}$)",
    "d": "Migrationsdauer (Jahre)",
}
HEADER = "% automatisch erzeugt von model/src/tables.py — nicht von Hand bearbeiten\n"
MINUS = r"\ensuremath{-}"


def de(x, nd=0, pct=False):
    """Deutsche Zahl: Dezimalkomma ({,} funktioniert in Text und Formel), Tausender mit
    schmalem Leerzeichen, echtes Minus."""
    if x is None:
        return "--"
    # kaufmännisch runden auf Basis der Dezimaldarstellung (vermeidet 0,6615 → 66,1 %)
    v = Decimal(repr(float(x))) * (100 if pct else 1)
    q = abs(v).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP)
    s = f"{q:,.{nd}f}".replace(",", "X").replace(".", "{,}").replace("X", r"\,")
    if v < 0 and q != 0:
        s = MINUS + s
    return s + (r"\,\%" if pct else "")


def share(x, nd=1):
    """Anteil in Prozent; kleine, aber positive Anteile als „< 0,1 %" statt „0,0 %"."""
    if x is not None and 0 < x < 0.5 * 10 ** (-nd) / 100:
        return r"<\," + de(10 ** (-nd - 2), nd, True)
    return de(x, nd, True)


def eur_tsd(x):
    return de(x / 1000)


def num(x):
    """Parameterwert kompakt: große Beträge mit Tausendertrennung, sonst 2 Nachkommastellen."""
    if abs(x) >= 1000:
        return de(x)
    return de(x, 2)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print("->", path.relative_to(ROOT.parent))


def tab_parameter():
    rows = []
    for u in UNCERTAIN:
        vals = (u.low, u.mode, u.high)
        if max(abs(v) for v in vals) >= 1000:
            cells = [de(v) for v in vals]
        else:  # so wenige Nachkommastellen wie nötig, innerhalb der Zeile einheitlich
            nd = next(k for k in (0, 1, 2) if all(abs(round(v, k) - v) < 1e-9 for v in vals))
            cells = [de(v, nd) for v in vals]
        cite = u.cite.replace("Annahme; Richtung:", "Annahme, Richtung:")
        rows.append(f"    ${SYMBOL_TEX[u.symbol]}$ & {SHORT_NAME[u.symbol]} & {cells[0]} & "
                    f"{cells[1]} & {cells[2]} & {ORIGIN[u.origin]} & {cite} \\\\")
    body = "\n".join(rows)
    return HEADER + rf"""\begin{{table}}[htbp]
  \centering
  \caption[Unsichere Modellparameter]{{Unsichere Modellparameter mit Minimum, Modus und Maximum
    der Beta-Verteilung sowie Herkunft (H = Bereich aus der Quelle hergeleitet, R = Richtung
    literaturgestützt, Höhe gesetzt, G = gesetzt). Skalenanker: $I_{{\mathrm{{M}}}} =
    {de(I_MONO)}$\,EUR, $N_0 = {de(N0)}$ Nutzer.}}
  \label{{tab:parameter}}
  \footnotesize
  \renewcommand{{\arraystretch}}{{1.08}}
  \begin{{tabular}}{{@{{}}l >{{\raggedright\arraybackslash}}p{{5.4cm}} r r r c
      >{{\raggedright\arraybackslash}}p{{3.8cm}}@{{}}}}
    \toprule
    Symbol & Bedeutung & Min. & Modus & Max. & Herk. & Beleg \\
    \midrule
{body}
    \bottomrule
  \end{{tabular}}
  \source{{Eigene Darstellung auf der Basis der in der Spalte \enquote{{Beleg}} genannten Quellen.}}
\end{{table}}
"""


def tab_szenarien(r):
    s = r["szenarien"]
    lines = []
    for name in ("niedrig", "mittel", "stark"):
        x = s[name]
        lines.append(
            f"    {name} & {de(x['g'], 0, True)} & {de(x['p'], 1)} & {eur_tsd(x['K_MS']['median'])} & "
            f"{eur_tsd(x['K_MF']['median'])} & {eur_tsd(x['delta']['median'])} & "
            f"{eur_tsd(x['delta']['mean'])} & "
            f"[{eur_tsd(x['delta']['q05'])}; {eur_tsd(x['delta']['q95'])}] & "
            f"{share(x['P_MS_guenstiger'])} \\\\")
    ev = s["EV"]
    lines.append("    \\midrule")
    lines.append(
        f"    gewichtet & & & {eur_tsd(ev['EV_MS']['median'])} & {eur_tsd(ev['EV_MF']['median'])} & "
        f"{eur_tsd(ev['delta']['median'])} & {eur_tsd(ev['delta']['mean'])} & "
        f"[{eur_tsd(ev['delta']['q05'])}; {eur_tsd(ev['delta']['q95'])}] & "
        f"{share(1 - ev['anteil_MF_guenstiger'], 2)} \\\\")
    body = "\n".join(lines)
    return HEADER + rf"""\begin{{table}}[htbp]
  \centering
  \caption[Barwertige Gesamtkosten je Szenario]{{Barwertige Gesamtkosten je Szenario und
    szenariogewichtet (Median über {de(N_RUNS)} Parametersätze, Tsd.\,EUR).
    $\Delta K = K_{{\mathrm{{MF}}}} - K_{{\mathrm{{MS}}}}$ als Median der Differenz je
    Parametersatz, Mittel: Mittelwert von $\Delta K$. Positive Werte bedeuten einen
    Kostenvorteil von MS.}}
  \label{{tab:szenarien}}
  \footnotesize
  \begin{{tabular}}{{@{{}}l r r r r r r c r@{{}}}}
    \toprule
    Szenario & $g$ & $p_j$ & $K_{{\mathrm{{MS}}}}$ & $K_{{\mathrm{{MF}}}}$ & $\Delta K$ &
      Mittel & 90-\%-Intervall & $P(\Delta K > 0)$ \\
    \midrule
{body}
    \bottomrule
  \end{{tabular}}
  \source{{Eigene Darstellung.}}
\end{{table}}
"""


def tab_hypothesen(r):
    h = r["hypothesen"]
    h3 = h["H3"]
    st = h3["stark"]["rang"]
    order = [z["symbol"] for z in sorted(r["sensitivitaet"]["prcc"],
                                         key=lambda z: -abs(z["prcc_dEV"]))]
    h3["wert"]["rang_h"] = order.index("h") + 1
    h3["wert"]["rang_mu"] = order.index("mu") + 1
    ci2 = h["H2"]["ci"]
    rows = [
        ("H1", r"Anteil der Parametersätze mit $EV_{\mathrm{MF}} < EV_{\mathrm{MS}}$ mindestens 80\,\%",
         f"{de(h['H1']['wert'], 2, True)}", h["H1"]["bestaetigt"]),
        ("H2", r"$P(\Delta K > 0 \mid g = 60\,\%)$ über 50\,\%",
         f"{de(h['H2']['wert'], 1, True)} (95-\\%-Konfidenzintervall der Monte-Carlo-Schätzung {de(ci2['lo'], 1, True)} bis "
         f"{de(ci2['hi'], 1, True)}), abhängig von Annahmen, siehe \\cref{{tab:robustheit_anhang}}",
         h["H2"]["bestaetigt"]),
        ("H3", r"$h$ und $\mu$ nach $|\mathrm{PRCC}|$ vor allen Parametern der laufenden Kosten",
         f"szenariogewichtet: $h$ Rang {h3['wert']['rang_h']}, $\\mu$ Rang "
         f"{h3['wert']['rang_mu']}, $\\Phi$ Rang 1. Starkes Szenario: "
         f"$h$ Rang {st['h']}, $\\mu$ Rang {st['mu']}", h3["bestaetigt"]),
    ]
    body = "\n    \\addlinespace\n".join(
        f"    {a} & {b} & {c} & {'gestützt' if d else 'nicht gestützt'} \\\\" for a, b, c, d in rows)
    return HEADER + rf"""\begin{{table}}[htbp]
  \centering
  \caption[Prüfung der Hypothesen]{{Prüfung der Hypothesen anhand der festgelegten
    Kriterien.}}
  \label{{tab:hypothesen}}
  \footnotesize
  \begin{{tabular}}{{@{{}}l >{{\raggedright\arraybackslash}}p{{5.2cm}}
      >{{\raggedright\arraybackslash}}p{{6.4cm}} l@{{}}}}
    \toprule
    & Kriterium & Ergebnis & Befund \\
    \midrule
{body}
    \bottomrule
  \end{{tabular}}
  \source{{Eigene Darstellung.}}
\end{{table}}
"""


VARIANT_LABEL = {
    "basis": r"Basisfall (\cref{tab:parameter})",
    "verpflichtung": "Beschlossene Migrationskosten voll angerechnet",
    "vorausschauend": "Vorausschauende Migration",
    "beides": "Voll angerechnet und vorausschauend",
    "h_klein": r"Kapazitätsreserve $h$: 2 / 4 / 10",
    "h_gross": r"Kapazitätsreserve $h$: 2 / 10 / 50",
    "phi_niedrig": r"Plattform-Grundlast niedrig: 5 / 15 / 30 Tsd.\,EUR",
    "phi_hoch": r"Plattform-Grundlast hoch: 60 / 100 / 150 Tsd.\,EUR",
    "skala5": r"Skalenanker $I_{\mathrm{M}} \times 5$ (2 Mio.\,EUR)",
    "lambda2": r"PERT $\lambda = 2$ (flacher)",
    "lambda6": r"PERT $\lambda = 6$ (spitzer)",
    "gleich": "Gleichverteilung",
    "zins0": r"Zinssatz 0\,\%",
    "zins10": r"Zinssatz 10\,\%",
    "T10": "Horizont 10 Jahre",
}

MAIN_VARIANTS = ("basis", "verpflichtung", "vorausschauend", "beides", "h_klein", "h_gross",
                 "phi_niedrig", "phi_hoch", "skala5", "gleich")


def _variant_row(v):
    band = (f"{de(v['g_P20'], 0, True)}--{de(v['g_P80'], 0, True)}"
            if v["g_P20"] is not None and v["g_P80"] is not None else "--")
    g50 = de(v["g_P50"], 0, True) if v["g_P50"] is not None else r"$>$\,100\,\%"
    return (f"    {VARIANT_LABEL.get(v['key'], v['key'])} & {de(v['H1'], 2, True)} & {de(v['H2'], 1, True)} & "
            f"{g50} & {band} \\\\")


def tab_robustheit(r, keys=MAIN_VARIANTS, label="tab:robustheit", appendix=False):
    rows = [v for v in r["varianten"] if v["key"] in keys]
    body = "\n".join(_variant_row(v) for v in rows)
    cap = ("Robustheitsprüfung über alle Varianten" if appendix
           else "Robustheit der Kernergebnisse gegenüber Modell- und Parameterannahmen")
    return HEADER + rf"""\begin{{table}}[htbp]
  \centering
  \caption[{cap}]{{{cap}. H1: Anteil der Parametersätze mit geringerem szenariogewichtetem
    EV für MF. H2: $P(\Delta K > 0)$ bei 60\,\% Wachstum. $g^*$: Wachstumsrate mit
    50\,\% Amortisationswahrscheinlichkeit. Übergang: 20 bis 80\,\%. Bereiche als
    Minimum / Modus / Maximum.}}
  \label{{{label}}}
  \footnotesize
  \begin{{tabular}}{{@{{}}>{{\raggedright\arraybackslash}}p{{9.2cm}} r r r c@{{}}}}
    \toprule
    Variante & H1 & H2 & $g^*$ & Übergang \\
    \midrule
{body}
    \bottomrule
  \end{{tabular}}
  \source{{Eigene Darstellung.}}
\end{{table}}
"""


def tab_sensitivitaet_anhang(r):
    sens = r["sensitivitaet"]
    eq = sens["prcc_rang_gleiche_breite"]
    mono = sens["monotonie"]
    rows = []
    for k, x in enumerate(sorted(sens["prcc"], key=lambda z: -abs(z["prcc_dEV"])), start=1):
        s = x["symbol"]
        rows.append(f"    ${SYMBOL_TEX[s]}$ & {de(x['prcc_dEV'], 2)} & {k} "
                    f"({x['rang_boot_lo']}--{x['rang_boot_hi']}) & {de(x['srrc2_dEV'], 1, True)} & "
                    f"{de(x['prcc_dK_stark'], 2)} & {de(x['srrc2_dK_stark'], 1, True)} & {eq[s]} & "
                    f"{de(mono[s], 1, True) if s in mono else '--'} \\\\")
    body = "\n".join(rows)
    r2 = r["hypothesen"]["H3"]["r2_rangregression"]
    return HEADER + rf"""\begin{{table}}[htbp]
  \centering
  \caption[Globale Sensitivität im Detail]{{Globale Sensitivität: PRCC und Rang (95-\%-Bootstrap-Intervall
    des Rangs), Varianzanteil SRRC$^2$ (Rangregression, $R^2$ = {de(r2['dEV'], 2)} bzw.
    {de(r2['dK_stark'], 2)}), Rang bei gleich breiten Bereichen (Modus $\pm$\,50\,\%) und Anteil
    der Parametersätze mit monotonem Verlauf von $\Delta EV$ im Parameter (--: nicht ausgewertet).}}
  \label{{tab:sensitivitaet_anhang}}
  \footnotesize
  \begin{{tabular}}{{@{{}}l r c r r r c r@{{}}}}
    \toprule
    & \multicolumn{{3}}{{c}}{{$\Delta EV$ (szenariogewichtet)}} &
      \multicolumn{{2}}{{c}}{{$\Delta K$ (60\,\%)}} & Rang bei & \\
    \cmidrule(lr){{2-4}}\cmidrule(lr){{5-6}}
    Parameter & PRCC & Rang & SRRC$^2$ & PRCC & SRRC$^2$ & gleicher Breite & monoton \\
    \midrule
{body}
    \bottomrule
  \end{{tabular}}
  \source{{Eigene Darstellung.}}
\end{{table}}
"""


def tab_seeds(r):
    """Anhang: Kernkennzahlen mit anderen Startwerten des Zufallszahlengenerators."""
    rows = []
    for k, x in enumerate(r["seed_stabilitaet"]):
        label = f"{x['seed']} (Basisfall)" if k == 0 else str(x["seed"])
        rows.append(f"    {label} & {de(x['H1'], 2, True)} & {de(x['H2'], 1, True)} & "
                    f"{de(x['g_P50'], 1, True)} & ${SYMBOL_TEX[x['prcc_rang1']]}$ \\\\")
    body = "\n".join(rows)
    return HEADER + rf"""\begin{{table}}[htbp]
  \centering
  \caption[Stabilität gegenüber dem Startwert]{{Kernkennzahlen bei unterschiedlichen Startwerten
    des Zufallszahlengenerators (je {de(N_RUNS)} Parametersätze). H1: Anteil der Parametersätze
    mit geringerem szenariogewichtetem Erwartungswert für MF. H2: $P(\Delta K > 0)$ bei 60\,\%
    Wachstum. $g^*$: Wachstumsrate mit 50\,\% Amortisationswahrscheinlichkeit.}}
  \label{{tab:seeds}}
  \footnotesize
  \begin{{tabular}}{{@{{}}l r r r c@{{}}}}
    \toprule
    Startwert & H1 & H2 & $g^*$ & Rang 1 nach $|\mathrm{{PRCC}}|$ \\
    \midrule
{body}
    \bottomrule
  \end{{tabular}}
  \source{{Eigene Darstellung.}}
\end{{table}}
"""


def macros(r):
    s, h, be = r["szenarien"], r["hypothesen"], r["breakeven"]
    sens = r["sensitivitaet"]
    hor = {row["T"]: row for row in sens["horizont"]}
    prcc = {row["symbol"]: row for row in sens["prcc"]}
    zins = {row["i"]: row for row in sens["zins"]}
    torn = {row["symbol"]: row for row in sens["tornado"]["zeilen"]}
    var = {v["key"]: v for v in r["varianten"]}
    mig, dec = r["migration"]["anteile"], r["migration"]["zerlegung_stark"]
    rank = h["H3"]["wert"]
    order = [x["symbol"] for x in sorted(sens["prcc"], key=lambda z: -abs(z["prcc_dEV"]))]
    eq = sens["prcc_rang_gleiche_breite"]
    struct = [var[k]["g_P50"] for k in ("basis", "verpflichtung", "vorausschauend", "beides")
              if var[k]["g_P50"] is not None]
    hvar = [var[k]["g_P50"] for k in ("h_klein", "basis", "h_gross") if var[k]["g_P50"] is not None]
    m = {
        "nRuns": de(N_RUNS), "seedValue": str(SEED), "pertLambda": de(PERT_LAMBDA),
        "HeinsAnteil": de(h["H1"]["wert"], 2, True),
        "HzweiP": de(h["H2"]["wert"], 1, True),
        "HzweiLo": de(h["H2"]["ci"]["lo"], 1, True), "HzweiHi": de(h["H2"]["ci"]["hi"], 1, True),
        "HzweiSE": de(h["H2"]["ci"]["se"] * 100, 1),
        "HdreiRangA": str(rank["schlechtester_rang_h_mu"]),
        "HdreiRangB": str(rank["bester_rang_betrieb"]),
        "gStern": de(be["kurve_schwellen"]["g_bei_P50"], 1, True),
        "gSternRund": de(be["kurve_schwellen"]["g_bei_P50"], 0, True),
        "gPzwanzig": de(be["kurve_schwellen"]["g_bei_P20"], 0, True),
        "gPachtzig": de(be["kurve_schwellen"]["g_bei_P80"], 0, True),
        "gZiehMedian": de(be["je_ziehung"]["g_star"]["median"], 0, True),
        "gZiehQfuenf": de(be["je_ziehung"]["g_star"]["q05"], 0, True),
        "gZiehQneunfuenf": de(be["je_ziehung"]["g_star"]["q95"], 0, True),
        "gZiehAnteil": de(be["je_ziehung"]["anteil_mit_breakeven_bis_gmax"], 1, True),
        "gZiehUneindeutig": de(be["je_ziehung"]["anteil_nicht_eindeutig"], 1, True),
        "gZiehOhne": de(1 - be["je_ziehung"]["anteil_mit_breakeven_bis_gmax"], 1, True),
        "gKapMedian": de(be["je_ziehung"]["g_kapazitaet"]["median"], 1, True),
        "rhoKap": de(be["je_ziehung"]["spearman_gstar_gcap"], 2),
        "gDiffMedian": de(be["je_ziehung"]["g_star_minus_g_cap"]["median"] * 100, 1),
        "PmsNiedrig": share(s["niedrig"]["P_MS_guenstiger"]),
        "PmsMittel": share(s["mittel"]["P_MS_guenstiger"], 2),
        "PmsStark": de(s["stark"]["P_MS_guenstiger"], 1, True),
        "dKNiedrig": eur_tsd(s["niedrig"]["delta"]["median"]),
        "dKMittel": eur_tsd(s["mittel"]["delta"]["median"]),
        "dKStark": eur_tsd(s["stark"]["delta"]["median"]),
        "dKStarkQfuenf": eur_tsd(s["stark"]["delta"]["q05"]),
        "dKStarkQneunfuenf": eur_tsd(s["stark"]["delta"]["q95"]),
        "EVms": eur_tsd(s["EV"]["EV_MS"]["median"]),
        "EVmf": eur_tsd(s["EV"]["EV_MF"]["median"]),
        "dEV": eur_tsd(s["EV"]["delta"]["median"]),
        "dEVMittel": eur_tsd(s["EV"]["delta"]["mean"]),
        "dEVQfuenf": eur_tsd(s["EV"]["delta"]["q05"]),
        "dEVQneunfuenf": eur_tsd(s["EV"]["delta"]["q95"]),
        "dEVBasis": eur_tsd(sens["tornado"]["dEV_basis"]),
        "trigMittel": de(mig["mittel"]["ausgeloest"], 1, True),
        "trigStark": de(mig["stark"]["ausgeloest"], 0, True),
        "fertigStark": de(mig["stark"]["abgeschlossen"], 0, True),
        "PmsAusgeloest": de(dec["P_MS_ausgeloest"], 0, True),
        "PmsNichtAusgeloest": de(dec["P_MS_nicht_ausgeloest"], 0, True),
        "gSternOhneGrenze": de(dec["g_bei_P50_ohne_grenze"], 0, True),
        "gSternTvier": de(hor[4]["g_bei_P50"], 0, True),
        "gSternTsechs": de(hor[6]["g_bei_P50"], 0, True),
        "gSternTzehn": de(hor[10]["g_bei_P50"], 0, True),
        "PmsStarkTdrei": de(hor[3]["P_MS_stark"], 1, True),
        "PmsStarkTzehn": de(hor[10]["P_MS_stark"], 1, True),
        "pStarkKritisch": de(sens["p_stark"]["p_stark_H1_kippt_unter_80"], 0, True),
        "pStarkMittelNull": de(sens["p_stark"]["p_stark_mean_dEV_null"], 0, True),
        "PmsStarkZinsNull": de(zins[0.0]["P_MS_stark"], 1, True),
        "PmsStarkZinsZehn": de(zins[0.1]["P_MS_stark"], 1, True),
        "tornPhiLow": eur_tsd(torn["Phi"]["dEV_low"]), "tornPhiHigh": eur_tsd(torn["Phi"]["dEV_high"]),
        "rangEins": f"${SYMBOL_TEX[order[0]]}$", "rangZwei": f"${SYMBOL_TEX[order[1]]}$",
        "rangDrei": f"${SYMBOL_TEX[order[2]]}$", "rangVier": f"${SYMBOL_TEX[order[3]]}$",
        "rangH": str(order.index("h") + 1), "rangMu": str(order.index("mu") + 1),
        "rangMuStark": str(h["H3"]["stark"]["rang"]["mu"]),
        "rangHStark": str(h["H3"]["stark"]["rang"]["h"]),
        "rangPhiGleich": str(eq["Phi"]), "rangHGleich": str(eq["h"]), "rangMuGleich": str(eq["mu"]),
        "Rzwei": de(h["H3"]["r2_rangregression"]["dEV"], 2),
        "monoD": de(sens["monotonie"]["d"], 0, True),
        "gSternStrukturMin": de(min(struct), 0, True), "gSternStrukturMax": de(max(struct), 0, True),
        "gSternHMin": de(min(hvar), 0, True), "gSternHMax": de(max(hvar), 0, True),
    }
    for sym in ("Phi", "omega", "kappa", "psi", "h", "mu", "d", "gamma_M", "beta_M"):
        key = {"Phi": "Phi", "omega": "Omega", "kappa": "Kappa", "psi": "Psi", "h": "H", "mu": "Mu",
               "d": "D", "gamma_M": "GammaM", "beta_M": "BetaM"}[sym]
        m[f"prcc{key}"] = de(prcc[sym]["prcc_dEV"], 2)
        m[f"varAnteil{key}"] = de(prcc[sym]["srrc2_dEV"], 0, True)
        m[f"varAnteil{key}Stark"] = de(prcc[sym]["srrc2_dK_stark"], 0, True)
    m["prccHStark"] = de(prcc["h"]["prcc_dK_stark"], 2)
    digits = {"0": "Null", "1": "Eins", "2": "Zwei", "5": "Fuenf", "6": "Sechs"}
    five_year = [v["H1"] for k, v in var.items() if k != "T10"]
    m["HeinsMinFuenfJahre"] = de(min(five_year), 1, True)
    p20 = [v["g_P20"] for k, v in var.items() if k != "T10" and v["g_P20"] is not None]
    m["gPzwanzigMinFuenfJahre"] = de(min(p20), 0, True)
    for k, v in var.items():
        name = "".join(digits.get(ch, ch) for ch in k.title() if ch.isalnum())
        m[f"var{name}Hzwei"] = de(v["H2"], 1, True)
        m[f"var{name}Heins"] = de(v["H1"], 1, True)
        m[f"var{name}gStern"] = de(v["g_P50"], 0, True) if v["g_P50"] is not None else r"über 100\,\%"
    heat = json.loads((DATA / "heatmap.json").read_text(encoding="utf-8"))
    names = {2.0: "Zwei", 5.0: "Fuenf", 10.0: "Zehn", 20.0: "Zwanzig"}
    for hv, row in zip(heat["h"], heat["P"]):
        if hv in names:
            m[f"gSternH{names[hv]}"] = de(crossing(heat["g"], row, 0.5), 0, True)
    # Ablesebeispiele aus der Heatmap (Anwendungsbeispiel in Kap. 5.2)
    for (gv, hv, name) in ((0.3, 5.0, "DreissigFuenf"), (0.6, 3.0, "SechzigDrei"),
                           (0.6, 10.0, "SechzigZehn")):
        gi, hi = heat["g"].index(gv), heat["h"].index(hv)
        m[f"heatP{name}"] = de(heat["P"][hi][gi], 0, True)
    # Nulldurchgang des Mittelwerts von ΔK über g (Bezug Erwartungswertprinzip ↔ 50-%-Kriterium)
    import csv
    with open(DATA / "wachstumskurve.csv", encoding="utf-8") as fh:
        rows_wk = list(csv.DictReader(fh))
    gk = [float(x["g"]) for x in rows_wk]
    m["gMittelNull"] = de(crossing(gk, [float(x["mean"]) for x in rows_wk], 0.0), 0, True)
    m["gMedianNull"] = de(crossing(gk, [float(x["median"]) for x in rows_wk], 0.0), 0, True)
    # Kostenzerlegung bei den wahrscheinlichsten Parameterwerten (Kap. 4.1)
    bf = r["basisfall"]
    lo, hi = bf["niedrig"], bf["stark"]
    m["bfNiedrigDiff"] = eur_tsd(lo["MS"]["gesamt"] - lo["MF"]["gesamt"])
    m["bfNiedrigInfra"] = eur_tsd(lo["MS"]["infrastruktur"] - lo["MF"]["infrastruktur"])
    m["bfNiedrigInv"] = eur_tsd(lo["MS"]["investition"] - lo["MF"]["investition"])
    m["bfNiedrigWart"] = eur_tsd(lo["MS"]["wartung"] - lo["MF"]["wartung"])
    m["bfStarkStart"] = de(hi["migrationsstart_jahr"], 1)
    m["bfStarkDiff"] = eur_tsd(hi["MF"]["gesamt"] - hi["MS"]["gesamt"])
    m["bfStarkMig"] = eur_tsd(hi["MF"]["skalierung_migration"])
    m["bfStarkMSSkal"] = eur_tsd(hi["MS"]["skalierung_migration"])
    # Plausibilisierung: Amortisationsdauer (Jahre) bei 60 % und 100 % Wachstum
    for key, name in (("0.60", "Stark"), ("1.00", "Hundert")):
        am = r["amortisationsdauer"][key]
        m[f"amort{name}Zwei"] = share(am["anteil_bis_2_jahre"])
        m[f"amort{name}Drei"] = share(am["anteil_bis_3_jahre"])
        m[f"amort{name}Fuenf"] = share(am["anteil_bis_5_jahre"])
        m[f"amort{name}Zehn"] = de(am["anteil_bis_10_jahre"], 0, True)
        m[f"amort{name}Median"] = de(am["dauer_amortisierender"]["median"], 1)
        m[f"amort{name}Qfuenf"] = de(am["dauer_amortisierender"]["q05"], 1)
        m[f"amort{name}Qneunfuenf"] = de(am["dauer_amortisierender"]["q95"], 1)
    # Seed-Stabilität: Spannweiten über alle Startwerte
    sd = r["seed_stabilitaet"]
    m["seedAnzahl"] = str(len(sd))
    for key, name, nd in (("H1", "Heins", 2), ("H2", "Hzwei", 1), ("g_P50", "gStern", 1)):
        vals = [x[key] for x in sd]
        m[f"seed{name}Min"] = de(min(vals), nd, True)
        m[f"seed{name}Max"] = de(max(vals), nd, True)
    lines = [HEADER.rstrip()]
    lines += [f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in m.items()]
    return "\n".join(lines) + "\n"


def main():
    r = json.loads((DATA / "results.json").read_text(encoding="utf-8"))
    TAB.mkdir(exist_ok=True)
    write(TAB / "tab_parameter.tex", tab_parameter())
    write(TAB / "tab_szenarien.tex", tab_szenarien(r))
    write(TAB / "tab_hypothesen.tex", tab_hypothesen(r))
    write(TAB / "tab_robustheit.tex", tab_robustheit(r))
    write(TAB / "tab_robustheit_anhang.tex",
          tab_robustheit(r, keys=[v["key"] for v in r["varianten"]],
                         label="tab:robustheit_anhang", appendix=True))
    write(TAB / "tab_sensitivitaet_anhang.tex", tab_sensitivitaet_anhang(r))
    write(TAB / "tab_seeds.tex", tab_seeds(r))
    write(TAB / "zahlen.tex", macros(r))


if __name__ == "__main__":
    main()
