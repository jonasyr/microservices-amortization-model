"""Abbildungen aus den gespeicherten Ergebnissen (output/data/).

Gestaltung: graustufentauglich (Linienart/Marker/Schraffur statt nur Farbe), kein Titel im
Bild, Arial 8–9 pt, deutsche Zahlenformatierung, Erzeugung in Endbreite (17 cm).
Aufruf (aus model/):  python -m src.figures
"""

import json
import shutil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.ticker import FuncFormatter, PercentFormatter  # noqa: E402

from .experiments import delta  # noqa: E402
from .params import N_RUNS, SCENARIOS, SEED, UNCERTAIN_BY_SYMBOL  # noqa: E402
from .sampling import sample  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "output" / "data"
OUT = ROOT / "output" / "figures"
PAPER_FIGS = ROOT.parent / "figures"

CM = 1 / 2.54
WIDTH = 17 * CM
GREY = {"dark": "0.15", "mid": "0.45", "light": "0.75", "pale": "0.9"}

plt.rcParams.update({
    "font.family": "Arial", "font.size": 8.5, "axes.labelsize": 8.5,
    "mathtext.fontset": "custom", "mathtext.rm": "Arial", "mathtext.it": "Arial:italic",
    "mathtext.bf": "Arial:bold", "mathtext.sf": "Arial", "mathtext.default": "it",
    "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.2, "grid.linewidth": 0.5,
    "lines.linewidth": 1.2, "pdf.fonttype": 42, "savefig.bbox": "tight",
})

SYMBOL_TEX = {
    "kappa": r"$\kappa$", "w": r"$w$", "omega": r"$\omega$", "gamma_M": r"$\gamma_{\mathrm{M}}$",
    "gamma_S": r"$\gamma_{\mathrm{S}}$", "F_M": r"$F_{\mathrm{M}}$", "Phi": r"$\Phi$",
    "V": r"$V$", "psi": r"$\psi$", "beta_M": r"$\beta_{\mathrm{M}}$",
    "beta_S": r"$\beta_{\mathrm{S}}$", "s": r"$s$", "h": r"$h$", "mu": r"$\mu$", "d": r"$d$",
}


def de(x, nd=0):
    s = f"{x:,.{nd}f}"
    return s.replace(",", "\u00a0").replace(".", ",").replace("-", "\u2212")


def tsd(ax, axis="y"):
    f = FuncFormatter(lambda v, _: de(v / 1000))
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(f)


def pct(ax, axis="x", nd=0):
    f = FuncFormatter(lambda v, _: de(v * 100, nd) + "\u00a0%")
    (ax.xaxis if axis == "x" else ax.yaxis).set_major_formatter(f)


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    PAPER_FIGS.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"{name}.{ext}", dpi=300)
    shutil.copy(OUT / f"{name}.pdf", PAPER_FIGS / f"{name}.pdf")
    plt.close(fig)


def fig_szenarien(p):
    """Abb.: Verteilung von ΔK je Szenario (Box + Streuband)."""
    fig, ax = plt.subplots(figsize=(WIDTH, 5.5 * CM))
    names = list(SCENARIOS)
    data = [delta(p, SCENARIOS[s]) for s in names]
    bp = ax.boxplot(data, orientation="horizontal", whis=(5, 95), showfliers=False, widths=0.5,
                    patch_artist=True, medianprops={"color": "black", "linewidth": 1.4})
    for patch in bp["boxes"]:
        patch.set(facecolor=GREY["pale"], edgecolor="black")
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_yticks(range(1, 4), [f"{s} ({de(SCENARIOS[s] * 100)}\u00a0%)" for s in names])
    ax.set_xlabel(r"$\Delta K = K_{\mathrm{MF}} - K_{\mathrm{MS}}$ (Tsd. EUR, Barwert)")
    tsd(ax, "x")
    ax.text(0.99, 0.02, "Microservices günstiger →", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=7.5, color=GREY["mid"])
    ax.text(0.01, 0.02, "← Monolith first günstiger", transform=ax.transAxes,
            ha="left", va="bottom", fontsize=7.5, color=GREY["mid"])
    save(fig, "abb_szenarien_delta")


def fig_wachstumskurve():
    """Kernabbildung: P(MS günstiger) über g (oben) und ΔK mit 90-%-Band (unten)."""
    c = pd.read_csv(DATA / "wachstumskurve.csv")
    thr = json.loads((DATA / "results.json").read_text(encoding="utf-8"))["breakeven"][
        "kurve_schwellen"]
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(WIDTH, 10 * CM), sharex=True,
                                 gridspec_kw={"height_ratios": [1.2, 1]})
    g = c["g"].to_numpy()
    lo, hi = thr["g_bei_P20"], thr["g_bei_P80"]
    for ax in (a1, a2):
        ax.axvspan(lo, hi, color=GREY["pale"], zorder=0)
    a1.plot(g, c["P_MS_guenstiger"], color="black")
    a1.axhline(0.5, color=GREY["mid"], linestyle=":", linewidth=0.9)
    a1.axvline(thr["g_bei_P50"], color=GREY["mid"], linestyle="--", linewidth=0.9)
    for s, gs in SCENARIOS.items():
        y = np.interp(gs, g, c["P_MS_guenstiger"])
        a1.plot(gs, y, marker="D", color="black", markersize=4.5, linestyle="none")
        a1.annotate(s, (gs, y), textcoords="offset points", xytext=(6, -12), fontsize=7.5)
    a1.set_ylabel("P(Microservices\ngünstiger)")
    a1.set_ylim(-0.02, 1.02)
    pct(a1, "y")
    a1.annotate(f"$g^*$ = {de(thr['g_bei_P50'] * 100, 1)}\u00a0%",
                (thr["g_bei_P50"], 0.5), textcoords="offset points", xytext=(6, -14),
                fontsize=7.5)
    a2.fill_between(g, c["q05"], c["q95"], color=GREY["light"], alpha=0.8, linewidth=0,
                    label="90-%-Intervall")
    a2.plot(g, c["median"], color="black", label="Median")
    a2.axhline(0, color="black", linewidth=0.8)
    a2.set_ylabel(r"$\Delta K$ (Tsd. EUR)")
    tsd(a2)
    a2.set_xlabel("jährliche Wachstumsrate der Nutzerzahl $g$")
    a2.set_xlim(0, 1)
    pct(a2, "x")
    a2.legend(loc="upper left", frameon=False)
    save(fig, "abb_wachstumskurve")


def fig_heatmap():
    """P(MS günstiger) über g × Kapazitätsreserve h."""
    hm = json.loads((DATA / "heatmap.json").read_text(encoding="utf-8"))
    g, h, P = np.array(hm["g"]), np.array(hm["h"]), np.array(hm["P"])
    fig, ax = plt.subplots(figsize=(WIDTH, 6.5 * CM))
    im = ax.pcolormesh(g, np.arange(len(h)), P, cmap="Greys", vmin=0, vmax=1,
                       shading="nearest")
    cs = ax.contour(g, np.arange(len(h)), P, levels=[0.2, 0.5, 0.8], colors="black",
                    linewidths=[0.7, 1.3, 0.7], linestyles=[":", "-", ":"])
    ax.clabel(cs, fmt=lambda v: de(v * 100) + "\u00a0%", fontsize=7)
    ax.set_yticks(np.arange(len(h)), [de(x) for x in h])
    ax.set_ylabel(r"Kapazitätsreserve $h = N_{\mathrm{krit}}/N_0$")
    ax.set_xlabel("jährliche Wachstumsrate der Nutzerzahl $g$")
    pct(ax, "x")
    ax.grid(False)
    cb = fig.colorbar(im, ax=ax, pad=0.02)
    cb.set_label("P(Microservices günstiger)")
    cb.ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: de(v * 100) + "\u00a0%"))
    save(fig, "abb_heatmap")


def fig_sensitivitaet():
    """Tornado (Basisfall, ΔEV) links, PRCC (global, ΔEV) rechts."""
    r = json.loads((DATA / "results.json").read_text(encoding="utf-8"))
    torn = r["sensitivitaet"]["tornado"]
    rows = torn["zeilen"][::-1]
    base = torn["dEV_basis"]
    prc = sorted(r["sensitivitaet"]["prcc"], key=lambda x: abs(x["prcc_dEV"]))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(WIDTH, 7.5 * CM),
                                 gridspec_kw={"width_ratios": [1.35, 1]})
    y = np.arange(len(rows))
    for k, row in enumerate(rows):
        lo, hi = row["dEV_low"], row["dEV_high"]
        a1.barh(k, lo - base, left=base, color=GREY["mid"], height=0.6,
                label="Minimum" if k == 0 else None)
        a1.barh(k, hi - base, left=base, color=GREY["light"], height=0.6, edgecolor="black",
                linewidth=0.4, label="Maximum" if k == 0 else None)
    a1.axvline(base, color="black", linewidth=0.8)
    a1.set_yticks(y, [SYMBOL_TEX[row["symbol"]] for row in rows])
    a1.set_xlabel(r"$\Delta EV$ (Tsd. EUR)")
    tsd(a1, "x")
    a1.legend(loc="lower left", frameon=False, title="Parameterwert", title_fontsize=7.5)
    a1.grid(axis="y", visible=False)
    y2 = np.arange(len(prc))
    vals = [x["prcc_dEV"] for x in prc]
    a2.barh(y2, vals, color=[GREY["dark"] if v > 0 else GREY["light"] for v in vals],
            edgecolor="black", linewidth=0.4, height=0.6)
    a2.axvline(0, color="black", linewidth=0.8)
    a2.set_yticks(y2, [SYMBOL_TEX[x["symbol"]] for x in prc])
    a2.set_xlim(-1, 1)
    a2.set_xlabel(r"PRCC mit $\Delta EV$")
    a2.xaxis.set_major_formatter(FuncFormatter(lambda v, _: de(v, 1)))
    a2.grid(axis="y", visible=False)
    fig.text(0.02, 0.98, "a", fontweight="bold", va="top")
    fig.text(0.60, 0.98, "b", fontweight="bold", va="top")
    save(fig, "abb_sensitivitaet")


def fig_anhang():
    """Anhang: Horizont, p_stark, Konvergenz, Break-even je Ziehung."""
    hor = pd.read_csv(DATA / "horizont.csv")
    ps = pd.read_csv(DATA / "p_stark.csv")
    be = np.load(DATA / "breakeven_je_ziehung.npz")
    r = json.loads((DATA / "results.json").read_text(encoding="utf-8"))
    fig, ax = plt.subplots(2, 2, figsize=(WIDTH, 11 * CM))
    a = ax[0, 0]
    a.plot(hor["T"], hor["g_bei_P50"], marker="o", color="black")
    a.set_xlabel("Betrachtungszeitraum $T$ (Jahre)")
    a.set_ylabel("$g^*$ (P = 50\u00a0%)")
    pct(a, "y")
    a = ax[0, 1]
    a.plot(ps["p_stark"], ps["anteil_MF_guenstiger"], color="black")
    a.axhline(0.8, color=GREY["mid"], linestyle=":")
    a.axvline(0.2, color=GREY["mid"], linestyle="--")
    a.set_xlabel(r"$p_{\mathrm{stark}}$")
    a.set_ylabel("Anteil EV(MF) < EV(MS)")
    pct(a, "x")
    pct(a, "y")
    a = ax[1, 0]
    conv = pd.DataFrame(r["konvergenz"])
    a.plot(conv["n"], conv["P_MS_stark"], marker="s", color="black", label="P(MS günstiger), stark")
    a.plot(conv["n"], conv["anteil_MF_guenstiger_EV"], marker="o", color=GREY["mid"],
           linestyle="--", label="Anteil EV(MF) < EV(MS)")
    a.set_xscale("log")
    a.set_xlabel("Anzahl Läufe")
    pct(a, "y")
    a.legend(frameon=False, fontsize=7)
    a = ax[1, 1]
    ok = ~np.isnan(be["g_star"])
    a.scatter(be["g_cap"][ok], be["g_star"][ok], s=2, color="black", alpha=0.15,
              rasterized=True)
    lim = [0, 1.2]
    a.plot(lim, lim, color=GREY["mid"], linestyle="--", linewidth=0.8)
    a.set_xlim(0.1, 1.0)
    a.set_ylim(0, 1.2)
    a.set_xlabel(r"$g_{\mathrm{kap}} = h^{1/T} - 1$")
    a.set_ylabel("$g^*$ je Ziehung")
    pct(a, "x")
    pct(a, "y")
    for k, axx in enumerate(ax.flat):
        axx.text(-0.18, 1.02, "abcd"[k], transform=axx.transAxes, fontweight="bold")
    fig.tight_layout()
    save(fig, "abb_anhang_robustheit")


def make_all(p=None):
    if p is None:
        p = sample(N_RUNS, np.random.default_rng(SEED))
    fig_szenarien(p)
    fig_wachstumskurve()
    fig_heatmap()
    fig_sensitivitaet()
    fig_anhang()
    print(f"Abbildungen -> {OUT} und {PAPER_FIGS}")


if __name__ == "__main__":
    make_all()
