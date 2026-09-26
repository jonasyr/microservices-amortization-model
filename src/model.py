"""Kostenmodell: barwertige Gesamtkosten beider Alternativen.

Alternativen
  MS  – Microservices von Beginn
  MF  – Monolith first mit Migrationsoption: Migration startet, sobald die Nutzerzahl die
        Kapazitätsgrenze h·N0 erreicht, dauert d Jahre (Parallelbetrieb), danach gilt die
        Kostenstruktur der Microservices-Architektur.

Zeitraster: Monate m = 1 … 12·T, Nutzerentwicklung N(m)/N0 = (1+g)^(m/12),
Diskontierung (1+i)^(-m/12). Die Anfangsinvestition fällt in m = 0 an.

Vier Kostenkategorien (Exposé): Anfangsinvestition, Wartung, Infrastruktur,
Skalierung/Migration (MS: Kapazitätsstufe s je Nutzerverdopplung; MF: Migration).

Alle Funktionen sind über Parameterziehungen vektorisiert: jeder Parameter ist ein
Array der Länge n (oder ein Skalar).
"""

import numpy as np

from .params import I_MONO

CATEGORIES = ("investition", "wartung", "infrastruktur", "skalierung_migration")


def _derived(p):
    """Abgeleitete Jahresgrößen aus den Modellparametern."""
    W_M = p["w"] * I_MONO
    return {
        "W_M": W_M,
        "W_S": W_M * (1 + p["omega"]),
        "F_M": p["F_M"],
        "F_S": p["F_M"] + p["Phi"],
        "V_M": p["V"],
        "V_S": p["V"] * (1 + p["psi"]),
        "I_MS": I_MONO * (1 + p["kappa"]),
        "M": p["mu"] * I_MONO,
    }


def _col(a):
    """Parameter als Spaltenvektor (n, 1) für Broadcasting über Monate."""
    return np.asarray(a, dtype=float).reshape(-1, 1)


def present_values(p, g, T=5, i=0.05, detail=False):
    """Barwertige Gesamtkosten K_MS und K_MF je Parameterziehung.

    p       dict Symbol -> Array (n,) oder Skalar
    g       Wachstumsrate p. a., Skalar oder Array (n,)
    Rückgabe: (K_MS, K_MF) als Arrays (n,); mit detail=True zusätzlich je Alternative
    ein dict der Barwerte je Kostenkategorie sowie das Migrationsstartjahr (NaN = keine).
    """
    q = _derived(p)
    n = max(np.size(v) for v in list(p.values()) + [g])
    months = np.arange(1, 12 * T + 1)
    t = months / 12.0
    x = (1.0 + _col(np.broadcast_to(g, (n,)))) ** t          # N(m)/N0, Form (n, M)
    disc = (1.0 + i) ** (-t)                                  # Form (M,)

    col = {k: _col(np.broadcast_to(v, (n,))) for k, v in q.items()}
    par = {k: _col(np.broadcast_to(p[k], (n,))) for k in ("gamma_M", "gamma_S", "beta_M",
                                                          "beta_S", "s", "h", "d", "Phi")}

    # laufende Kosten je Monat (Jahreswerte / 12)
    mono_wart = col["W_M"] * x ** par["gamma_M"] / 12
    mono_infra = (col["F_M"] + col["V_M"] * x ** par["beta_M"]) / 12
    ms_wart = col["W_S"] * x ** par["gamma_S"] / 12
    ms_infra = (col["F_S"] + col["V_S"] * x ** par["beta_S"]) / 12

    # Kapazitätsstufen Microservices: s je vollendeter Verdopplung gegenüber N0
    k = np.floor(np.log2(x))
    steps = par["s"] * np.diff(k, axis=1, prepend=0.0)

    # --- Alternative MS ---------------------------------------------------------
    ms = {
        "investition": q["I_MS"] * np.ones(n),
        "wartung": (ms_wart * disc).sum(axis=1),
        "infrastruktur": (ms_infra * disc).sum(axis=1),
        "skalierung_migration": (steps * disc).sum(axis=1),
    }

    # --- Alternative MF ---------------------------------------------------------
    reached = x >= par["h"]
    has_trigger = reached.any(axis=1)
    m_c = np.where(has_trigger, reached.argmax(axis=1) + 1, np.inf)   # Auslösemonat
    elapsed = months[None, :] - m_c[:, None]                          # Monate seit Auslösung
    mig_len = 12.0 * par["d"]
    frac_mig = np.where(elapsed >= 1, np.clip(mig_len - (elapsed - 1), 0.0, 1.0), 0.0)
    frac_post = np.where(elapsed >= 1, 1.0 - frac_mig, 0.0)
    frac_pre = 1.0 - frac_mig - frac_post

    mig_rate = col["M"] / mig_len                                     # Migrationsaufwand je Monat
    mono_share = frac_pre + frac_mig                                  # Monolith läuft bis Abschluss
    mf = {
        "investition": I_MONO * np.ones(n),
        "wartung": ((mono_share * mono_wart + frac_post * ms_wart) * disc).sum(axis=1),
        "infrastruktur": ((mono_share * mono_infra + frac_mig * par["Phi"] / 12
                           + frac_post * ms_infra) * disc).sum(axis=1),
        "skalierung_migration": ((frac_mig * mig_rate + (frac_post > 0) * steps)
                                 * disc).sum(axis=1),
    }

    K_MS = sum(ms.values())
    K_MF = sum(mf.values())
    if detail:
        start_year = np.where(has_trigger, m_c / 12.0, np.nan)
        return K_MS, K_MF, {"MS": ms, "MF": mf, "migrationsstart_jahr": start_year}
    return K_MS, K_MF


def delta(p, g, T=5, i=0.05):
    """ΔK = K_MF − K_MS; positive Werte: Microservices von Beginn ist günstiger."""
    K_MS, K_MF = present_values(p, g, T=T, i=i)
    return K_MF - K_MS
