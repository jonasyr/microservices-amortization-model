"""Erzeugt LaTeX-Tabellen und Zahlen-Makros aus output/data/results.json.

Jede Zahl im Fließtext wird über ein Makro aus tabellen/zahlen.tex gesetzt, damit Text,
Tabellen und Abbildungen dieselbe Quelle haben.
Aufruf (aus model/):  python -m src.tables
"""

import json
from pathlib import Path

from .analysis import crossing
from .params import I_MONO, N0, N_RUNS, SEED, UNCERTAIN

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "output" / "data"
TAB = ROOT.parent / "tabellen"

ORIGIN = {"hergeleitet": "H", "relation_belegt": "R", "gesetzt": "G"}
SYMBOL_TEX = {
    "kappa": r"\kappa", "w": "w", "omega": r"\omega", "gamma_M": r"\gamma_{\mathrm{M}}",
    "gamma_S": r"\gamma_{\mathrm{S}}", "F_M": r"F_{\mathrm{M}}", "Phi": r"\Phi", "V": "V",
    "psi": r"\psi", "beta_M": r"\beta_{\mathrm{M}}", "beta_S": r"\beta_{\mathrm{S}}",
    "s": "s", "h": "h", "mu": r"\mu", "d": "d",
}
SHORT_NAME = {
    "kappa": "Mehraufwand Erstentwicklung MS (Anteil an $I_{\\mathrm{M}}$)",
    "w": "Wartung p.\\,a. bei $N_0$ (Anteil an $I_{\\mathrm{M}}$)",
    "omega": "Wartungsmehraufwand MS",
    "gamma_M": "Wartungsexponent Monolith",
    "gamma_S": "Wartungsexponent MS",
    "F_M": "Infrastruktur-Fixkosten Monolith (EUR/a)",
    "Phi": "Plattform-Grundlast MS (EUR/a)",
    "V": "lastabh. Infrastruktur bei $N_0$ (EUR/a)",
    "psi": "Abweichung lastabh. Infrastruktur MS",
    "beta_M": "Infrastrukturexponent Monolith",
    "beta_S": "Infrastrukturexponent MS",
    "s": "Kapazitätsstufe MS je Verdopplung (EUR)",
    "h": "Kapazitätsreserve Monolith ($N_{\\mathrm{krit}}/N_0$)",
    "mu": "Migrationskosten (Vielfaches von $I_{\\mathrm{M}}$)",
    "d": "Migrationsdauer (Jahre)",
}
CITE = {
    "kappa": r"\textcite[S.~30]{taibi2017}", "omega": r"\textcite{soldani2018}",
    "gamma_M": r"\textcite{richards2020}", "gamma_S": r"\textcite{richards2020}",
    "Phi": r"\textcite{soldani2018}", "psi": r"\textcite{villamizar2016}; \textcite{blinowski2022}",
    "beta_M": r"\textcite{gunther2007}; \textcite{blinowski2022}",
    "beta_S": r"\textcite{hassan2022}", "h": r"\textcite{gunther2007}",
    "d": r"\textcite{fritzsch2019}",
}


def de(x, nd=0, pct=False):
    """Deutsche Zahl: Dezimalkomma, Tausender mit schmalem Leerzeichen, echtes Minus."""
    if x is None:
        return "--"
    v = x * 100 if pct else x
    s = f"{abs(v):,.{nd}f}".replace(",", "X").replace(".", ",").replace("X", "\\,")
    s = ("$-$" if v < 0 and float(f"{abs(v):.{nd}f}") != 0 else "") + s
    return s + ("\\,\\%" if pct else "")


def eur_tsd(x):
    return de(x / 1000)


def num(x):
    """Parameterwert kompakt: große Beträge mit Tausendertrennung, sonst 2 Nachkommastellen."""
    if abs(x) >= 1000:
        return de(x)
    return de(x, 2)


def macro_name(key):
    return "\\" + key


def write(path, text):
    path.write_text(text, encoding="utf-8")
    print("->", path.relative_to(ROOT.parent))


def tab_parameter():
    rows = []
    for u in UNCERTAIN:
        cite = CITE.get(u.symbol, "Annahme")
        rows.append(f"    ${SYMBOL_TEX[u.symbol]}$ & {SHORT_NAME[u.symbol]} & {num(u.low)} & "
                    f"{num(u.mode)} & {num(u.high)} & {ORIGIN[u.origin]} & {cite} \\\\")
    body = "\n".join(rows)
    return rf"""% automatisch erzeugt von model/src/tables.py — nicht von Hand bearbeiten
\begin{{table}}[htbp]
  \centering
  \caption[Unsichere Modellparameter]{{Unsichere Modellparameter mit Beta-Verteilung
    (Minimum, Modus, Maximum) und Herkunft (H = aus Quelle hergeleitet, R = Relation
    literaturgestützt, Höhe gesetzt, G = gesetzt). Skalenanker: $I_{{\mathrm{{M}}}} =
    {de(I_MONO)}$\,EUR, $N_0 = {de(N0)}$ Nutzer.}}
  \label{{tab:parameter}}
  \footnotesize
  \begin{{tabular}}{{@{{}}l p{{5.6cm}} r r r c p{{3.3cm}}@{{}}}}
    \toprule
    Symbol & Bedeutung & Min. & Modus & Max. & Herk. & Beleg \\
    \midrule
{body}
    \bottomrule
  \end{{tabular}}
  \source{{Eigene Darstellung.}}
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
            f"[{eur_tsd(x['delta']['q05'])}; {eur_tsd(x['delta']['q95'])}] & "
            f"{de(x['P_MS_guenstiger'], 1, True)} \\\\")
    ev = s["EV"]
    lines.append("    \\midrule")
    lines.append(
        f"    Erwartungswert & & & {eur_tsd(ev['EV_MS']['median'])} & {eur_tsd(ev['EV_MF']['median'])} & "
        f"{eur_tsd(ev['delta']['median'])} & [{eur_tsd(ev['delta']['q05'])}; {eur_tsd(ev['delta']['q95'])}] & "
        f"{de(1 - ev['anteil_MF_guenstiger'], 2, True)} \\\\")
    body = "\n".join(lines)
    return rf"""% automatisch erzeugt von model/src/tables.py — nicht von Hand bearbeiten
\begin{{table}}[htbp]
  \centering
  \caption[Barwertige Gesamtkosten je Szenario und Erwartungswert]{{Barwertige
    Gesamtkosten je Szenario und Erwartungswert (Median über {de(N_RUNS)} Ziehungen, Tsd.\,EUR).
    $\Delta K = K_{{\mathrm{{MF}}}} - K_{{\mathrm{{MS}}}}$; positive Werte bedeuten einen
    Kostenvorteil von Microservices von Beginn.}}
  \label{{tab:szenarien}}
  \footnotesize
  \begin{{tabular}}{{@{{}}l r r r r r c r@{{}}}}
    \toprule
    Szenario & $g$ & $p_i$ & $K_{{\mathrm{{MS}}}}$ & $K_{{\mathrm{{MF}}}}$ & $\Delta K$ &
      90-\%-Intervall $\Delta K$ & P(MS günstiger) \\
    \midrule
{body}
    \bottomrule
  \end{{tabular}}
  \source{{Eigene Berechnung.}}
\end{{table}}
"""


def tab_hypothesen(r):
    h = r["hypothesen"]
    h3 = h["H3"]["wert"]
    rows = [
        ("H1", r"Anteil der Ziehungen mit $EV_{\mathrm{MF}} < EV_{\mathrm{MS}}$ $\geq 80\,\%$",
         de(h["H1"]["wert"], 2, True), h["H1"]["bestaetigt"]),
        ("H2", r"$P(\Delta K > 0 \mid g = 60\,\%) > 50\,\%$",
         de(h["H2"]["wert"], 1, True), h["H2"]["bestaetigt"]),
        ("H3", r"Rang von $h$ und $\mu$ nach $|\mathrm{PRCC}|$ vor allen Betriebskostenparametern",
         f"schlechtester Rang $h$/$\\mu$: {h3['schlechtester_rang_h_mu']}; "
         f"bester Betriebskostenrang: {h3['bester_rang_betrieb']}", h["H3"]["bestaetigt"]),
    ]
    body = "\n".join(f"    {a} & {b} & {c} & {'gestützt' if d else 'nicht gestützt'} \\\\"
                     for a, b, c, d in rows)
    return rf"""% automatisch erzeugt von model/src/tables.py — nicht von Hand bearbeiten
\begin{{table}}[htbp]
  \centering
  \caption[Prüfung der Hypothesen]{{Prüfung der Hypothesen anhand der vor der Simulation
    festgelegten Kriterien.}}
  \label{{tab:hypothesen}}
  \footnotesize
  \begin{{tabular}}{{@{{}}l p{{6.2cm}} p{{4.6cm}} l@{{}}}}
    \toprule
    & Kriterium & Ergebnis & Befund \\
    \midrule
{body}
    \bottomrule
  \end{{tabular}}
  \source{{Eigene Berechnung.}}
\end{{table}}
"""


def macros(r):
    s, h, be = r["szenarien"], r["hypothesen"], r["breakeven"]
    sens = r["sensitivitaet"]
    hor = {row["T"]: row for row in sens["horizont"]}
    prcc = {row["symbol"]: row for row in sens["prcc"]}
    zins = {row["i"]: row for row in sens["zins"]}
    torn = {row["symbol"]: row for row in sens["tornado"]["zeilen"]}
    rank = h["H3"]["wert"]
    m = {
        "nRuns": de(N_RUNS), "seedValue": str(SEED),
        "HeinsAnteil": de(h["H1"]["wert"], 2, True),
        "HzweiP": de(h["H2"]["wert"], 1, True),
        "HdreiRangA": str(rank["schlechtester_rang_h_mu"]),
        "HdreiRangB": str(rank["bester_rang_betrieb"]),
        "gStern": de(be["kurve_schwellen"]["g_bei_P50"], 1, True),
        "gPzwanzig": de(be["kurve_schwellen"]["g_bei_P20"], 1, True),
        "gPachtzig": de(be["kurve_schwellen"]["g_bei_P80"], 1, True),
        "gZiehMedian": de(be["je_ziehung"]["g_star"]["median"], 1, True),
        "gZiehQfuenf": de(be["je_ziehung"]["g_star"]["q05"], 1, True),
        "gZiehQneunfuenf": de(be["je_ziehung"]["g_star"]["q95"], 1, True),
        "gZiehAnteil": de(be["je_ziehung"]["anteil_mit_breakeven_bis_gmax"], 1, True),
        "gKapMedian": de(be["je_ziehung"]["g_kapazitaet"]["median"], 1, True),
        "rhoKap": de(be["je_ziehung"]["spearman_gstar_gcap"], 2),
        "gDiffMedian": de(be["je_ziehung"]["g_star_minus_g_cap"]["median"] * 100, 1),
        "gDiffQfuenf": de(be["je_ziehung"]["g_star_minus_g_cap"]["q05"] * 100, 1),
        "PmsNiedrig": de(s["niedrig"]["P_MS_guenstiger"], 1, True),
        "PmsMittel": de(s["mittel"]["P_MS_guenstiger"], 2, True),
        "PmsStark": de(s["stark"]["P_MS_guenstiger"], 1, True),
        "dKNiedrig": eur_tsd(s["niedrig"]["delta"]["median"]),
        "dKMittel": eur_tsd(s["mittel"]["delta"]["median"]),
        "dKStark": eur_tsd(s["stark"]["delta"]["median"]),
        "dKStarkQfuenf": eur_tsd(s["stark"]["delta"]["q05"]),
        "dKStarkQneunfuenf": eur_tsd(s["stark"]["delta"]["q95"]),
        "EVms": eur_tsd(s["EV"]["EV_MS"]["median"]),
        "EVmf": eur_tsd(s["EV"]["EV_MF"]["median"]),
        "dEV": eur_tsd(s["EV"]["delta"]["median"]),
        "dEVQfuenf": eur_tsd(s["EV"]["delta"]["q05"]),
        "dEVQneunfuenf": eur_tsd(s["EV"]["delta"]["q95"]),
        "dEVBasis": eur_tsd(sens["tornado"]["dEV_basis"]),
        "gSternTvier": de(hor[4]["g_bei_P50"], 1, True),
        "gSternTsechs": de(hor[6]["g_bei_P50"], 1, True),
        "gSternTsieben": de(hor[7]["g_bei_P50"], 1, True),
        "gSternTzehn": de(hor[10]["g_bei_P50"], 1, True),
        "PmsStarkTdrei": de(hor[3]["P_MS_stark"], 1, True),
        "PmsStarkTzehn": de(hor[10]["P_MS_stark"], 1, True),
        "HeinsTzehn": de(hor[10]["anteil_MF_guenstiger_EV"], 1, True),
        "pStarkKritisch": de(sens["p_stark"]["p_stark_H1_kippt_unter_80"], 1, True),
        "pStarkMittelNull": de(sens["p_stark"]["p_stark_mean_dEV_null"], 1, True),
        "PmsStarkZinsNull": de(zins[0.0]["P_MS_stark"], 1, True),
        "PmsStarkZinsZehn": de(zins[0.1]["P_MS_stark"], 1, True),
        "prccPhi": de(prcc["Phi"]["prcc_dEV"], 2), "prccOmega": de(prcc["omega"]["prcc_dEV"], 2),
        "prccKappa": de(prcc["kappa"]["prcc_dEV"], 2), "prccPsi": de(prcc["psi"]["prcc_dEV"], 2),
        "prccH": de(prcc["h"]["prcc_dEV"], 2), "prccMu": de(prcc["mu"]["prcc_dEV"], 2),
        "prccGammaM": de(prcc["gamma_M"]["prcc_dEV"], 2),
        "prccBetaM": de(prcc["beta_M"]["prcc_dEV"], 2), "prccD": de(prcc["d"]["prcc_dEV"], 2),
        "prccHStark": de(prcc["h"]["prcc_dK_stark"], 2),
        "prccMuStark": de(prcc["mu"]["prcc_dK_stark"], 2),
        "rangMu": str(rank_of(sens["prcc"], "mu")), "rangH": str(rank_of(sens["prcc"], "h")),
        "rangMuStark": str(h["H3"]["stark"]["rang"]["mu"]),
        "tornPhiLow": eur_tsd(torn["Phi"]["dEV_low"]), "tornPhiHigh": eur_tsd(torn["Phi"]["dEV_high"]),
    }
    heat = json.loads((DATA / "heatmap.json").read_text(encoding="utf-8"))
    names = {2.0: "Zwei", 5.0: "Fuenf", 10.0: "Zehn", 20.0: "Zwanzig"}
    for hv, row in zip(heat["h"], heat["P"]):
        if hv in names:
            m[f"gSternH{names[hv]}"] = de(crossing(heat["g"], row, 0.5), 1, True)
    lines = ["% automatisch erzeugt von model/src/tables.py — nicht von Hand bearbeiten"]
    lines += [f"\\newcommand{{{macro_name(k)}}}{{{v}}}" for k, v in m.items()]
    return "\n".join(lines) + "\n"


def rank_of(table, symbol):
    order = sorted(table, key=lambda r: -abs(r["prcc_dEV"]))
    return 1 + [r["symbol"] for r in order].index(symbol)


def main():
    r = json.loads((DATA / "results.json").read_text(encoding="utf-8"))
    TAB.mkdir(exist_ok=True)
    write(TAB / "tab_parameter.tex", tab_parameter())
    write(TAB / "tab_szenarien.tex", tab_szenarien(r))
    write(TAB / "tab_hypothesen.tex", tab_hypothesen(r))
    write(TAB / "zahlen.tex", macros(r))


if __name__ == "__main__":
    main()
