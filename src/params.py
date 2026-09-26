"""Modellparameter: feste Größen, Szenarien und unsichere Parameter (PERT).

Jeder unsichere Parameter trägt (min, Modus, max) und eine Herkunftskennung:
  "hergeleitet"      Wert/Bereich aus einer Quelle abgeleitet
  "relation_belegt"  Richtung/Relation literaturgestützt, Höhe gesetzt
  "gesetzt"          freie, offen gekennzeichnete Annahme

Alle Geldbeträge in EUR pro Jahr bzw. einmalig. Die Ergebnisgrößen (Wahrscheinlichkeiten,
Break-even-Wachstumsraten) sind invariant gegenüber einer gemeinsamen Skalierung aller
Geldbeträge; die absolute Höhe dient nur der Anschaulichkeit.
"""

from dataclasses import dataclass

SEED = 20260926
N_RUNS = 10_000

# --- feste Größen -------------------------------------------------------------
T_YEARS = 5                 # Betrachtungszeitraum (Exposé)
DISCOUNT_RATE = 0.05        # Kalkulationszins p. a. (Konvention, in SA variiert)
N0 = 10_000                 # Ausgangsnutzerzahl (Normierungsgröße)

# Wachstumsszenarien und Eintrittswahrscheinlichkeiten (Exposé)
SCENARIOS = {"niedrig": 0.05, "mittel": 0.20, "stark": 0.60}
SCENARIO_PROBS = {"niedrig": 0.3, "mittel": 0.5, "stark": 0.2}

# Referenzwert der Erstentwicklung des Monolithen (Skalenanker, EUR)
I_MONO = 400_000


@dataclass(frozen=True)
class Uncertain:
    symbol: str
    name: str
    low: float
    mode: float
    high: float
    unit: str
    origin: str
    source: str
    group: str   # "kapazitaet_migration" | "betrieb" | "investition"


UNCERTAIN = [
    # Investition
    Uncertain("kappa", "Mehraufwand Erstentwicklung Microservices (Anteil von I_Mono)",
              0.10, 0.30, 0.60, "–", "relation_belegt",
              "richards2020; razzaq2023 (höhere Anfangsinvestition)", "investition"),
    # Wartung
    Uncertain("w", "Wartungskosten p. a. im Ausgangszustand (Anteil von I_Mono)",
              0.15, 0.20, 0.30, "–", "gesetzt",
              "Annahme; Wartungswachstum lehman1980", "betrieb"),
    Uncertain("omega", "Wartungsmehraufwand Microservices im Ausgangszustand",
              0.10, 0.30, 0.60, "–", "relation_belegt",
              "soldani2018; razzaq2023 (Betriebs-/DevOps-Overhead)", "betrieb"),
    Uncertain("gamma_M", "Wartungsexponent Monolith",
              0.40, 0.60, 0.80, "–", "relation_belegt",
              "richards2020; comstock2011 (Kopplung, Skalenunwirtschaftlichkeit)", "betrieb"),
    Uncertain("gamma_S", "Wartungsexponent Microservices",
              0.20, 0.35, 0.50, "–", "relation_belegt",
              "richards2020 (Entkopplung)", "betrieb"),
    # Infrastruktur
    Uncertain("F_M", "Infrastruktur-Fixkosten Monolith p. a.",
              6_000, 12_000, 20_000, "EUR/a", "gesetzt",
              "Annahme", "betrieb"),
    Uncertain("Phi", "Plattform-Grundlast Microservices p. a. (zusätzlich zu F_M)",
              20_000, 40_000, 80_000, "EUR/a", "relation_belegt",
              "soldani2018 (Orchestrierung, Observability); Höhe gesetzt", "betrieb"),
    Uncertain("V", "lastabhängige Infrastrukturkosten Monolith p. a. bei N0",
              20_000, 30_000, 45_000, "EUR/a", "gesetzt",
              "Annahme", "betrieb"),
    Uncertain("psi", "relative Abweichung lastabhängiger Infrastrukturkosten Microservices",
              -0.40, 0.00, 0.30, "–", "hergeleitet",
              "villamizar2017 (günstiger) vs. ueda2016, blinowski2022 (teurer)", "betrieb"),
    Uncertain("beta_M", "Infrastrukturexponent Monolith",
              0.90, 1.10, 1.40, "–", "relation_belegt",
              "gunther2007 (nichtlineare Skalierung); blinowski2022 (≤ 1 möglich)", "betrieb"),
    Uncertain("beta_S", "Infrastrukturexponent Microservices",
              0.85, 0.95, 1.05, "–", "relation_belegt",
              "hassan2022 (horizontale Skalierung annähernd proportional)", "betrieb"),
    Uncertain("s", "Kapazitätsstufe Microservices je Nutzerverdopplung",
              5_000, 20_000, 50_000, "EUR", "gesetzt",
              "Annahme", "betrieb"),
    # Kapazität und Migration
    Uncertain("h", "Kapazitätsreserve des Monolithen (Kapazitätsgrenze / N0)",
              2.0, 5.0, 20.0, "–", "gesetzt",
              "Existenz: gunther2007; Höhe gesetzt", "kapazitaet_migration"),
    Uncertain("mu", "Migrationskosten (Vielfaches von I_Mono)",
              0.50, 1.00, 2.00, "–", "gesetzt",
              "Annahme; Größenordnung gouigoux2017, faustino2024", "kapazitaet_migration"),
    Uncertain("d", "Migrationsdauer",
              1.0, 2.0, 3.0, "Jahre", "hergeleitet",
              "fritzsch2019 (1,5 bis über 3 Jahre)", "kapazitaet_migration"),
]

UNCERTAIN_BY_SYMBOL = {u.symbol: u for u in UNCERTAIN}


def modes() -> dict:
    """Modalwerte aller unsicheren Parameter (Basisfall)."""
    return {u.symbol: u.mode for u in UNCERTAIN}
