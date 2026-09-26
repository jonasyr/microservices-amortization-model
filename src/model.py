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

Modellentscheidungen mit Varianten (Robustheit):
  horizon = "cutoff"     nur Zahlungen bis T (Basisfall); eine über T hinausreichende
                         Migration geht anteilig ein
            "committed"  zusätzlich der Rest der bei Auslösung beschlossenen Migrationskosten M
                         (planmäßig über die Migrationsdauer verteilt und diskontiert)
  trigger = "reactive"   Migration startet bei Erreichen der Kapazitätsgrenze (Basisfall)
            "proactive"  Migration startet so früh, dass sie bei Erreichen der Grenze
                         abgeschlossen ist (Auslösung bei h / (1+g)^d)
Kapazitätsstufen, die MS bis zum Abschluss der Migration bereits bezahlt hat, gelten bei MF
als in den Migrationskosten M enthalten; nach Abschluss fallen nur neue Stufen an.
"""

import numpy as np

from .params import I_MONO

CATEGORIES = ("investition", "wartung", "infrastruktur", "skalierung_migration")


def _derived(p):
    """Abgeleitete Jahresgrößen aus den Modellparametern.

    Optional überschreibt p["I_M"] den Skalenanker I_MONO (Variante „Skalenanker × 5").
    """
    I_M = p.get("I_M", I_MONO)
    W_M = p["w"] * I_M
    return {
        "I_M": I_M,
        "W_M": W_M,
        "W_S": W_M * (1 + p["omega"]),
        "F_M": p["F_M"],
        "F_S": p["F_M"] + p["Phi"],
        "V_M": p["V"],
        "V_S": p["V"] * (1 + p["psi"]),
        "I_MS": I_M * (1 + p["kappa"]),
        "M": p["mu"] * I_M,
    }


def _col(a):
    """Parameter als Spaltenvektor (n, 1) für Broadcasting über Monate."""
    return np.asarray(a, dtype=float).reshape(-1, 1)


def present_values(p, g, T=5, i=0.05, detail=False, horizon="cutoff", trigger="reactive"):
    """Barwertige Gesamtkosten K_MS und K_MF je Parameterziehung.

    p       dict Symbol -> Array (n,) oder Skalar
    g       Wachstumsrate p. a., Skalar oder Array (n,)
    horizon "cutoff" | "committed", trigger "reactive" | "proactive" (siehe Moduldoku)
    Rückgabe: (K_MS, K_MF) als Arrays (n,); mit detail=True zusätzlich je Alternative
    ein dict der Barwerte je Kostenkategorie, das Migrationsstartjahr (NaN = keine) und
    der Abschlusszeitpunkt der Migration in Jahren (NaN = keine).
    """
    if horizon not in ("cutoff", "committed") or trigger not in ("reactive", "proactive"):
        raise ValueError("unbekannte Modellvariante")
    q = _derived(p)
    n = max(np.size(v) for v in list(p.values()) + [g])
    months = np.arange(1, 12 * T + 1)
    t = months / 12.0
    g_col = _col(np.broadcast_to(g, (n,)))
    x = (1.0 + g_col) ** t                                    # N(m)/N0, Form (n, M)
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
    threshold = par["h"]
    if trigger == "proactive":
        threshold = par["h"] / (1.0 + g_col) ** par["d"]
    reached = x >= threshold
    has_trigger = reached.any(axis=1)
    m_c = np.where(has_trigger, reached.argmax(axis=1) + 1, np.inf)   # Auslösemonat
    elapsed = months[None, :] - m_c[:, None]                          # Monate seit Auslösung
    mig_len = 12.0 * par["d"]
    frac_mig = np.where(elapsed >= 1, np.clip(mig_len - (elapsed - 1), 0.0, 1.0), 0.0)
    frac_post = np.where(elapsed >= 1, 1.0 - frac_mig, 0.0)
    frac_pre = 1.0 - frac_mig - frac_post

    mig_rate = col["M"] / mig_len                                     # Migrationsaufwand je Monat
    mono_share = frac_pre + frac_mig                                  # Monolith läuft bis Abschluss
    migration = (frac_mig * mig_rate * disc).sum(axis=1)
    if horizon == "committed":
        # Rest der beschlossenen Migrationskosten nach T, planmäßig verteilt und diskontiert
        tail = np.arange(12 * T + 1, 12 * T + int(np.ceil(12 * np.max(p["d"]))) + 2)
        el_tail = tail[None, :] - m_c[:, None]
        frac_tail = np.where(el_tail >= 1, np.clip(mig_len - (el_tail - 1), 0.0, 1.0), 0.0)
        migration = migration + (frac_tail * mig_rate * (1.0 + i) ** (-tail / 12.0)).sum(axis=1)
    mf = {
        "investition": q["I_M"] * np.ones(n),
        "wartung": ((mono_share * mono_wart + frac_post * ms_wart) * disc).sum(axis=1),
        "infrastruktur": ((mono_share * mono_infra + frac_mig * par["Phi"] / 12
                           + frac_post * ms_infra) * disc).sum(axis=1),
        "skalierung_migration": migration + (((frac_post > 0) * steps) * disc).sum(axis=1),
    }

    K_MS = sum(ms.values())
    K_MF = sum(mf.values())
    if detail:
        start_year = np.where(has_trigger, m_c / 12.0, np.nan)
        end_year = np.where(has_trigger, (m_c + mig_len[:, 0]) / 12.0, np.nan)
        return K_MS, K_MF, {"MS": ms, "MF": mf, "migrationsstart_jahr": start_year,
                            "migrationsende_jahr": end_year}
    return K_MS, K_MF


def delta(p, g, T=5, i=0.05, horizon="cutoff", trigger="reactive"):
    """ΔK = K_MF − K_MS; positive Werte: Microservices von Beginn ist günstiger."""
    K_MS, K_MF = present_values(p, g, T=T, i=i, horizon=horizon, trigger=trigger)
    return K_MF - K_MS
