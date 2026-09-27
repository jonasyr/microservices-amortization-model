"""Abbildungen aus den gespeicherten Ergebnissen (output/data/).

Gestaltung (IU-Formalia und Barrierefreiheit nach WCAG 2.2):
- Arial, mind. 8 pt in Endgröße, Erzeugung in Textbreite (17 cm), kein Titel im Bild
  (Beschriftung und Quelle im LaTeX-Dokument), deutsche Zahlenformatierung.
- Jede Achse benennt Größe, Symbol und Einheit („… in %", „… in Tsd. EUR").
- Text nur in Schwarz (19,7 : 1) oder Dunkelgrau (7,9 : 1) -> Kontrast AAA (≥ 7 : 1).
- Bedeutungstragende Grafikelemente ≥ 3 : 1 gegen Weiß (WCAG 1.4.11): Dunkelblau 8,1 : 1,
  Dunkelorange 5,3 : 1; helle Flächen nur ergänzend und stets mit kontrastreicher Kante.
- Farbe nie alleiniger Informationsträger (WCAG 1.4.1): zusätzlich Position, Linienart,
  Markerform oder Direktbeschriftung; Palette auf Farbfehlsichtigkeit geprüft
  (validate_palette.js: #184f95/#b8461a, ΔE 20,5 Protan) und in Graustufen unterscheidbar.
Aufruf (aus model/):  python -m src.figures
"""

import json
import shutil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patheffects as pe  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.ticker import FuncFormatter, MultipleLocator  # noqa: E402

from .analysis import crossing  # noqa: E402
from .experiments import delta  # noqa: E402
from .params import N_RUNS, SCENARIOS, SEED  # noqa: E402
from .sampling import sample  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "output" / "data"
OUT = ROOT / "output" / "figures"
# Innerhalb der Projektarbeit werden die PDFs zusätzlich ins LaTeX-Projekt kopiert
PAPER_FIGS = ROOT.parent / "figures" if (ROOT.parent / "main.tex").exists() else None

CM = 1 / 2.54
WIDTH = 17 * CM

# Farben (Kontrast gegen Weiß in Klammern)
INK = "#0b0b0b"         # Text, Nulllinien (19,7 : 1)
INK2 = "#52514e"        # Sekundärtext, Bezugslinien (7,9 : 1)
AXIS = "#52514e"        # Achsen und Ticks
GRID = "#e1e0d9"        # Gitter (dekorativ)
BLUE = "#184f95"        # Hauptreihe (8,1 : 1)
ORANGE = "#b8461a"      # Akzent/zweite Reihe (5,3 : 1)
BLUE_FILL = "#cde2fb"   # Flächen, nur ergänzend mit blauer Kante
BLUE_RAMP = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
SEQ = LinearSegmentedColormap.from_list("iu_blau", BLUE_RAMP)

FS = 8.5      # Achsenbeschriftung
FS_S = 8      # Ticks, Legende, Annotationen (Minimum)

plt.rcParams.update({
    "font.family": "Arial", "font.size": FS, "axes.labelsize": FS,
    "axes.labelcolor": INK, "text.color": INK,
    "mathtext.fontset": "custom", "mathtext.rm": "Arial", "mathtext.it": "Arial:italic",
    "mathtext.bf": "Arial:bold", "mathtext.sf": "Arial", "mathtext.default": "it",
    "xtick.labelsize": FS_S, "ytick.labelsize": FS_S, "legend.fontsize": FS_S,
    "xtick.color": AXIS, "ytick.color": AXIS, "xtick.labelcolor": INK, "ytick.labelcolor": INK,
    "xtick.major.size": 3, "ytick.major.size": 3, "xtick.major.width": 0.6,
    "ytick.major.width": 0.6, "xtick.minor.visible": False, "ytick.minor.visible": False,
    "axes.edgecolor": AXIS, "axes.linewidth": 0.6, "axes.labelpad": 4,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "axes.grid.axis": "y", "axes.axisbelow": True,
    "grid.color": GRID, "grid.linewidth": 0.5, "grid.linestyle": "-",
    "lines.linewidth": 1.6, "lines.solid_capstyle": "round",
    "legend.frameon": False, "legend.handlelength": 2.2,
    "pdf.fonttype": 42, "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
})

SYMBOL_TEX = {
    "kappa": r"$\kappa$", "w": r"$w$", "omega": r"$\omega$", "gamma_M": r"$\gamma_{\mathrm{M}}$",
    "gamma_S": r"$\gamma_{\mathrm{S}}$", "F_M": r"$F_{\mathrm{M}}$", "Phi": r"$\Phi$",
    "V": r"$V$", "psi": r"$\psi$", "beta_M": r"$\beta_{\mathrm{M}}$",
    "beta_S": r"$\beta_{\mathrm{S}}$", "s": r"$s$", "h": r"$h$", "mu": r"$\mu$", "d": r"$d$",
}
G_LABEL = r"Jährliche Wachstumsrate der Nutzerzahl $g$ in %"
HALO = [pe.withStroke(linewidth=2.5, foreground="white")]


def de(x, nd=0):
    s = f"{x:,.{nd}f}"
    return s.replace(",", " ").replace(".", ",").replace("-", "−")


def fmt_tsd(ax, axis="y"):
    """Achse in Tsd. EUR (Einheit steht in der Achsenbeschriftung)."""
    f = FuncFormatter(lambda v, _: de(v / 1000))
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(f)


def fmt_pct(ax, axis="x", nd=0, absolute=False):
    """Anteile als Prozentzahlen ohne %-Zeichen (Einheit steht in der Achsenbeschriftung)."""
    f = FuncFormatter(lambda v, _: de(abs(v) * 100 if absolute else v * 100, nd))
    (ax.xaxis if axis == "x" else ax.yaxis).set_major_formatter(f)


def panel(ax, letter, x=-0.1, y=1.04):
    ax.text(x, y, letter, transform=ax.transAxes, fontweight="bold", fontsize=9.5,
            ha="left", va="bottom")


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        meta = {"CreationDate": None} if ext == "pdf" else {}
        fig.savefig(OUT / f"{name}.{ext}", dpi=300, metadata=meta)  # reproduzierbare Dateien
    if PAPER_FIGS is not None:
        PAPER_FIGS.mkdir(parents=True, exist_ok=True)
        shutil.copy(OUT / f"{name}.pdf", PAPER_FIGS / f"{name}.pdf")
    plt.close(fig)


def fig_szenarien(p):
    """Anhang: Verteilung von ΔK je Szenario (Box: Quartile, Antennen: 5.–95. Perzentil)."""
    fig, ax = plt.subplots(figsize=(WIDTH, 5.2 * CM))
    names = list(SCENARIOS)[::-1]          # stark oben
    data = [delta(p, SCENARIOS[s]) for s in names]
    ax.axvline(0, color=INK, linewidth=0.8, zorder=1)
    ax.boxplot(data, orientation="horizontal", whis=(5, 95), showfliers=False, widths=0.52,
               patch_artist=True,
               boxprops={"facecolor": BLUE_FILL, "edgecolor": BLUE, "linewidth": 0.9},
               whiskerprops={"color": BLUE, "linewidth": 0.9},
               capprops={"color": BLUE, "linewidth": 0.9},
               medianprops={"color": INK, "linewidth": 1.6}, zorder=2)
    for k, d in enumerate(data, start=1):
        q95 = np.percentile(d, 95)
        ax.text(q95, k, f"  Median {de(np.median(d) / 1000)}", va="center", ha="left",
                fontsize=FS_S, color=INK2)
    ax.set_yticks(range(1, 4), [f"{s} ({de(SCENARIOS[s] * 100)} % p. a.)"
                                for s in names])
    ax.set_ylabel("Wachstumsszenario")
    ax.set_xlabel(r"Kostendifferenz $\Delta K$ = $K_{\mathrm{MF}}$ − $K_{\mathrm{MS}}$ "
                  r"in Tsd. EUR (Barwert)")
    fmt_tsd(ax, "x")
    ax.grid(axis="x", visible=True)
    ax.grid(axis="y", visible=False)
    lo = min(np.percentile(d, 5) for d in data)
    hi = max(np.percentile(d, 95) for d in data)
    ax.set_xlim(lo - 0.04 * (hi - lo), hi + 0.30 * (hi - lo))
    ax.text(0.995, 1.02, "MS günstiger →", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=FS_S, color=INK2)
    ax.text(0.0, 1.02, "← MF günstiger", transform=ax.transAxes,
            ha="left", va="bottom", fontsize=FS_S, color=INK2)
    save(fig, "abb_szenarien_delta")


def fig_wachstumskurve():
    """Kernabbildung: (a) Anteil ΔK > 0 über g, (b) Median und 90-%-Intervall von ΔK."""
    c = pd.read_csv(DATA / "wachstumskurve.csv")
    thr = json.loads((DATA / "results.json").read_text(encoding="utf-8"))["breakeven"][
        "kurve_schwellen"]
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(WIDTH, 9.2 * CM), sharex=True,
                                 gridspec_kw={"height_ratios": [1.15, 1], "hspace": 0.28})
    g = c["g"].to_numpy()
    lo, hi, gs = thr["g_bei_P20"], thr["g_bei_P80"], thr["g_bei_P50"]

    for ax in (a1, a2):
        ax.axvspan(lo, hi, color="#eef4fc", zorder=0, linewidth=0)
        for x in (lo, hi):
            ax.axvline(x, color=INK2, linewidth=0.6, linestyle=(0, (1, 2)), zorder=1)
        ax.axvline(gs, color=ORANGE, linewidth=1.1, linestyle=(0, (4, 2)), zorder=3)

    # (a) Wahrscheinlichkeitskurve
    a1.axhline(0.5, color=INK2, linewidth=0.6, linestyle=(0, (1, 2)), zorder=1)
    a1.plot(g, c["P_MS_guenstiger"], color=BLUE, zorder=4)
    a1.plot(gs, 0.5, marker="o", markersize=5.5, color=ORANGE, markeredgecolor="white",
            markeredgewidth=1, zorder=5)
    a1.annotate(rf"$g^{{\!*}}$ = {de(gs * 100, 1)} %", (gs, 0.5), textcoords="offset points",
                xytext=(7, -13), fontsize=FS_S, path_effects=HALO)
    a1.text((lo + hi) / 2, 1.07, "Übergangsbereich (20–80 %)", ha="center", va="bottom",
            fontsize=FS_S, color=INK2)
    for s, gsz in SCENARIOS.items():
        y = np.interp(gsz, g, c["P_MS_guenstiger"])
        a1.plot(gsz, y, marker="D", markersize=5, color=BLUE, markeredgecolor="white",
                markeredgewidth=0.8, linestyle="none", zorder=5)
        off = (0, 8) if y < 0.5 else (9, -3)
        a1.annotate(f"{s}\n({de(y * 100, 1)} %)" if y > 0.001 else s, (gsz, y),
                    textcoords="offset points", xytext=off, fontsize=FS_S,
                    ha="center" if y < 0.5 else "left", va="bottom" if y < 0.5 else "top",
                    path_effects=HALO)
    a1.set_ylabel("Anteil der Parametersätze\n" r"mit $\Delta K$ > 0 in %")
    a1.set_ylim(-0.03, 1.05)
    a1.yaxis.set_major_locator(MultipleLocator(0.25))
    fmt_pct(a1, "y")
    panel(a1, "a", x=-0.085)

    # (b) Kostendifferenz
    a2.fill_between(g, c["q05"], c["q95"], color=BLUE_FILL, linewidth=0, zorder=2,
                    label="90-%-Intervall (5.–95. Perzentil)")
    for q in ("q05", "q95"):
        a2.plot(g, c[q], color=BLUE, linewidth=0.6, zorder=3)
    a2.plot(g, c["median"], color=BLUE, zorder=4, label="Median")
    a2.axhline(0, color=INK, linewidth=0.8, zorder=3)
    a2.text(0.005, 0.02 * (c["q95"].max() - c["q05"].min()), r"$\Delta K$ > 0: MS günstiger", fontsize=FS_S, color=INK2, va="bottom", ha="left")
    a2.set_ylabel(r"Kostendifferenz $\Delta K$" "\nin Tsd. EUR (Barwert)")
    fmt_tsd(a2)
    a2.set_xlabel(G_LABEL)
    a2.set_xlim(0, 1)
    a2.xaxis.set_major_locator(MultipleLocator(0.1))
    fmt_pct(a2, "x")
    a2.legend(loc="upper left", bbox_to_anchor=(0, 1.04))
    panel(a2, "b", x=-0.085)
    fig.align_ylabels((a1, a2))
    save(fig, "abb_wachstumskurve")


def fig_heatmap():
    """Anteil ΔK > 0 über g × Kapazitätsreserve h, Isolinien 20/50/80 %."""
    hm = json.loads((DATA / "heatmap.json").read_text(encoding="utf-8"))
    g, h, P = np.array(hm["g"]), np.array(hm["h"]), np.array(hm["P"])
    rows = np.arange(len(h))
    fig, ax = plt.subplots(figsize=(WIDTH, 6.0 * CM))
    im = ax.pcolormesh(g, rows, P, cmap=SEQ, vmin=0, vmax=1, shading="nearest",
                       edgecolors="white", linewidth=0.4)
    cs = ax.contour(g, rows, P, levels=[0.2, 0.5, 0.8], colors=INK,
                    linewidths=[0.8, 1.6, 0.8], linestyles="-")
    for coll in (cs.collections if hasattr(cs, "collections") else [cs]):
        coll.set_path_effects([pe.withStroke(linewidth=2.8, foreground="white"), pe.Normal()])
    spots = []
    for level, row in ((0.2, 7), (0.5, 4), (0.8, 1)):
        xg = crossing(g, P[row], level)
        if xg is not None:
            spots.append((xg, row))
    labels = ax.clabel(cs, fmt=lambda v: de(v * 100) + " %", fontsize=FS_S, manual=spots,
                       inline_spacing=5, colors=INK)
    for t in labels:
        t.set_bbox({"facecolor": "white", "edgecolor": "none", "pad": 0.8})
    ax.set_yticks(rows, [de(x) for x in h])
    ax.set_ylabel("Kapazitätsreserve des Monolithen\n"
                  r"$h$ = $N_{\mathrm{krit}}/N_0$ (Vielfaches der Ausgangslast)")
    ax.set_xlabel(G_LABEL)
    ax.xaxis.set_major_locator(MultipleLocator(0.1))
    fmt_pct(ax, "x")
    ax.grid(False)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(length=0, pad=4)
    cb = fig.colorbar(im, ax=ax, pad=0.02, fraction=0.035, aspect=22)
    cb.set_label(r"Anteil der Parametersätze mit $\Delta K$ > 0 in %", fontsize=FS)
    cb.set_ticks([0, 0.2, 0.5, 0.8, 1])
    cb.ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: de(v * 100)))
    cb.outline.set_visible(False)
    cb.ax.tick_params(length=2.5, width=0.6, color=AXIS)
    for lv, lw in ((0.2, 0.8), (0.5, 1.6), (0.8, 0.8)):
        cb.ax.axhline(lv, color=INK, linewidth=lw)
    save(fig, "abb_heatmap")


def _param_value(sym, v):
    if abs(v) >= 1000:
        return de(v / 1000) + " Tsd."
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return s.replace(".", ",").replace("-", "−")


def fig_sensitivitaet():
    """(a) Tornado (lokal, ΔEV), (b) gerichtete Varianzanteile SRRC² (global, ΔEV)."""
    r = json.loads((DATA / "results.json").read_text(encoding="utf-8"))
    torn = r["sensitivitaet"]["tornado"]
    rows = torn["zeilen"][::-1]
    base = torn["dEV_basis"]
    prc = sorted(r["sensitivitaet"]["prcc"], key=lambda x: x["srrc2_dEV"])
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(WIDTH, 7.6 * CM),
                                 gridspec_kw={"width_ratios": [1.3, 1], "wspace": 0.32})
    # (a) Tornado mit Parameterwerten an den Balkenenden
    y = np.arange(len(rows))
    span = max(max(abs(rw["dEV_low"] - base), abs(rw["dEV_high"] - base)) for rw in rows)
    for k, rw in enumerate(rows):
        for key, val, col, lab in (("dEV_low", rw["low"], BLUE, "Minimum"),
                                   ("dEV_high", rw["high"], ORANGE, "Maximum")):
            x = rw[key]
            a1.barh(k, x - base, left=base, color=col, height=0.66, edgecolor="white",
                    linewidth=0.6, label=lab if k == len(rows) - 1 else None, zorder=2)
            if abs(x - base) > 1:
                right = x > base
                a1.text(x + (0.02 if right else -0.02) * span, k, _param_value(rw["symbol"], val),
                        va="center", ha="left" if right else "right", fontsize=FS_S,
                        color=INK2)
    a1.axvline(base, color=INK, linewidth=0.9, zorder=3)
    a1.set_xlim(base - 1.55 * span, base + 2.2 * span)
    a1.set_ylim(-0.7, len(rows) - 0.3)
    a1.set_yticks(y, [SYMBOL_TEX[rw["symbol"]] for rw in rows], fontsize=FS)
    a1.set_xlabel(r"$\Delta EV$ = $EV_{\mathrm{MF}}$ − $EV_{\mathrm{MS}}$ in Tsd. EUR")
    fmt_tsd(a1, "x")
    a1.grid(axis="y", visible=False)
    a1.grid(axis="x", visible=True)
    a1.tick_params(axis="y", length=0)
    a1.spines["left"].set_visible(False)
    a1.legend(loc="center right", title="Parameterwert", title_fontsize=FS_S, alignment="left",
              handlelength=1.2, handleheight=1.0, borderaxespad=0.1)
    panel(a1, "a", x=-0.09, y=1.02)

    # (b) Varianzanteile, Richtung durch Position (links: begünstigt MF, rechts: MS)
    y2 = np.arange(len(prc))
    signed = np.array([np.sign(x["prcc_dEV"]) * x["srrc2_dEV"] for x in prc])
    a2.barh(y2, signed, color=INK2, height=0.66,
            edgecolor="white", linewidth=0.6, zorder=2)
    m = np.abs(signed).max()
    for k, v in enumerate(signed):
        lab = de(abs(v) * 100) if abs(v) >= 0.005 else "< 1"
        a2.text(v + (1 if v >= 0 else -1) * 0.025 * m, k, lab, va="center",
                ha="left" if v >= 0 else "right", fontsize=FS_S, color=INK2)
    a2.axvline(0, color=INK, linewidth=0.9, zorder=3)
    lim = m * 1.3
    a2.set_xlim(-lim, lim)
    a2.set_ylim(-0.7, len(prc) - 0.3)
    a2.xaxis.set_major_locator(MultipleLocator(0.1))
    a2.set_yticks(y2, [SYMBOL_TEX[x["symbol"]] for x in prc], fontsize=FS)
    a2.set_xlabel(r"Varianzanteil an $\Delta EV$ (SRRC$^2$) in %")
    fmt_pct(a2, "x", absolute=True)
    a2.grid(axis="y", visible=False)
    a2.grid(axis="x", visible=True)
    a2.tick_params(axis="y", length=0)
    a2.spines["left"].set_visible(False)
    a2.text(0.48, 1.02, "← begünstigt MF", transform=a2.transAxes,
            ha="right", va="bottom", fontsize=FS_S, color=INK2)
    a2.text(0.52, 1.02, "begünstigt MS →", transform=a2.transAxes,
            ha="left", va="bottom", fontsize=FS_S, color=INK2)
    panel(a2, "b", x=-0.09, y=1.02)
    save(fig, "abb_sensitivitaet")


def fig_anhang():
    """Anhang: (a) Horizont, (b) p_stark, (c) Konvergenz, (d) Break-even je Ziehung."""
    hor = pd.read_csv(DATA / "horizont.csv")
    ps = pd.read_csv(DATA / "p_stark.csv")
    be = np.load(DATA / "breakeven_je_ziehung.npz")
    r = json.loads((DATA / "results.json").read_text(encoding="utf-8"))
    fig, ax = plt.subplots(2, 2, figsize=(WIDTH, 12.5 * CM),
                           gridspec_kw={"hspace": 0.55, "wspace": 0.32})

    a = ax[0, 0]
    ok = hor["g_bei_P50"].notna()
    a.plot(hor["T"][ok], hor["g_bei_P50"][ok], color=BLUE, marker="o", markersize=4.5,
           markeredgecolor="white", markeredgewidth=0.8)
    b5 = hor[hor["T"] == 5]["g_bei_P50"].iloc[0]
    a.plot(5, b5, marker="o", markersize=6.5, color=ORANGE, markeredgecolor="white",
           markeredgewidth=1, zorder=5)
    a.annotate("Basisfall", (5, b5), textcoords="offset points", xytext=(7, 3), fontsize=FS_S)
    a.set_xlabel(r"Horizont $T$ in Jahren")
    a.set_ylabel("Break-even-Wachstumsrate\n" r"$g^{\!*}$ in %")
    a.xaxis.set_major_locator(MultipleLocator(1))
    a.set_ylim(0, None)
    fmt_pct(a, "y")
    a.grid(axis="x", visible=True)

    a = ax[0, 1]
    a.axhline(0.8, color=INK2, linewidth=0.8, linestyle=(0, (1, 2)))
    a.text(0.99, 0.815, "Kriterium H1 (80 %)", fontsize=FS_S, color=INK2, ha="right",
           va="bottom", path_effects=HALO)
    a.axvline(0.2, color=ORANGE, linewidth=1.1, linestyle=(0, (4, 2)))
    a.text(0.215, 0.05, "Annahme\nExposé (20 %)", fontsize=FS_S, color=INK, ha="left",
           va="bottom", path_effects=HALO)
    a.plot(ps["p_stark"], ps["anteil_MF_guenstiger"], color=BLUE)
    a.set_xlabel(r"Wahrscheinlichkeit des starken Szenarios $p_{\mathrm{stark}}$ in %")
    a.set_ylabel(r"Anteil mit $EV_{\mathrm{MF}}$ < $EV_{\mathrm{MS}}$ in %")
    a.set_ylim(0, 1.03)
    a.set_xlim(0, ps["p_stark"].max())
    fmt_pct(a, "x")
    fmt_pct(a, "y")
    a.grid(axis="x", visible=True)

    a = ax[1, 0]
    conv = pd.DataFrame(r["konvergenz"])
    a.plot(conv["n"], conv["anteil_MF_guenstiger_EV"], marker="o", markersize=4, color=BLUE,
           markeredgecolor="white", markeredgewidth=0.6,
           label=r"Anteil $EV_{\mathrm{MF}}$ < $EV_{\mathrm{MS}}$")
    a.plot(conv["n"], conv["P_MS_stark"], marker="s", markersize=4, color=ORANGE,
           linestyle=(0, (4, 2)), markeredgecolor="white", markeredgewidth=0.6,
           label=r"Anteil $\Delta K$ > 0, starkes Szenario")
    a.set_xscale("log")
    a.xaxis.set_major_formatter(FuncFormatter(lambda v, _: de(v)))
    a.set_xlabel(r"Anzahl der Parametersätze $n$ (logarithmische Skala)")
    a.set_ylabel("Kennzahl in %")
    a.set_ylim(0.5, 1.03)
    fmt_pct(a, "y")
    a.legend(loc="center right", fontsize=FS_S, handlelength=2.6)
    a.grid(axis="x", visible=True)

    a = ax[1, 1]
    okb = ~np.isnan(be["g_star"])
    a.scatter(be["g_cap"][okb], be["g_star"][okb], s=2.5, color=BLUE, alpha=0.18,
              linewidths=0, rasterized=True)
    lim = [0, 1.5]
    a.plot(lim, lim, color=INK, linestyle=(0, (4, 2)), linewidth=0.9)
    a.text(0.93, 0.96, r"$g^{\!*}$ = $g_{\mathrm{kap}}$", fontsize=FS_S, ha="right", va="bottom",
           rotation=0, path_effects=HALO)
    a.set_xlim(0.1, 1.0)
    a.set_ylim(0, 1.5)
    a.yaxis.set_major_locator(MultipleLocator(0.25))
    a.set_xlabel(r"Wachstumsrate bis zur Kapazitätsgrenze $g_{\mathrm{kap}}$ in %")
    a.set_ylabel(r"$g^{\!*}$ je Parametersatz in %")
    fmt_pct(a, "x")
    fmt_pct(a, "y")
    a.grid(axis="x", visible=True)

    for k, axx in enumerate(ax.flat):
        panel(axx, "abcd"[k], x=-0.2, y=1.03)
    fig.align_ylabels(ax[:, 0])
    fig.align_ylabels(ax[:, 1])
    save(fig, "abb_anhang_robustheit")


def make_all(p=None):
    if p is None:
        p = sample(N_RUNS, np.random.default_rng(SEED))
    fig_szenarien(p)
    fig_wachstumskurve()
    fig_heatmap()
    fig_sensitivitaet()
    fig_anhang()
    print(f"Abbildungen -> {OUT}" + (f" und {PAPER_FIGS}" if PAPER_FIGS else ""))


if __name__ == "__main__":
    make_all()
