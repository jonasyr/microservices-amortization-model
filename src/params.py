"""Modellparameter: feste Größen, Szenarien und unsichere Parameter (PERT).

Jeder unsichere Parameter trägt (min, Modus, max) und eine Herkunftskennung:
  "hergeleitet"      Bereich folgt aus der zitierten Stelle
  "relation_belegt"  Richtung/Relation literaturgestützt, Höhe bzw. Breite gesetzt
  "gesetzt"          freie, offen gekennzeichnete Annahme

`cite` ist die einzige Belegangabe je Parameter (LaTeX, wird unverändert in Tab. 2
übernommen); `note` begründet Abweichungen des Bereichs von der Quelle.

Geldbeträge in EUR pro Jahr bzw. einmalig. κ, w und μ sind relativ zu I_M definiert,
Φ, F_M, V und s absolut; die Ergebnisse gelten daher für die Größenordnung des
Skalenankers I_M (siehe Robustheitsvariante „Skalenanker × 5").
"""

from dataclasses import dataclass

SEED = 20260926
N_RUNS = 10_000
PERT_LAMBDA = 4.0           # Formparameter der Beta-PERT-Verteilung (Standardwert)

# --- feste Größen -------------------------------------------------------------
T_YEARS = 5                 # Betrachtungszeitraum (Exposé)
DISCOUNT_RATE = 0.05        # Kalkulationszins p. a. (Konvention, in SA 0–10 % variiert)
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
    cite: str
    note: str
    group: str   # "kapazitaet_migration" | "betrieb" | "investition"


UNCERTAIN = [
    # Investition
    Uncertain("kappa", "Mehraufwand Erstentwicklung Microservices (Anteil von I_M)",
              0.00, 0.25, 0.30, "–", "hergeleitet",
              r"\textcite[S.~30]{taibi2017}",
              "Quelle: 24 % der Befragten 0–10 %, 76 % 20–30 % Mehraufwand", "investition"),
    # Wartung
    Uncertain("w", "Wartungskosten p. a. im Ausgangszustand (Anteil von I_M)",
              0.15, 0.20, 0.30, "–", "gesetzt", "Annahme", "", "betrieb"),
    Uncertain("omega", "Entwicklungs- und Wartungsmehraufwand Microservices",
              0.05, 0.20, 0.40, "–", "relation_belegt",
              r"\textcite[S.~27]{taibi2017}",
              "Quelle: Mehraufwand von knapp 20 %; Breite gesetzt", "betrieb"),
    Uncertain("gamma_M", "Wartungsexponent Monolith",
              0.40, 0.60, 0.80, "–", "gesetzt", "Annahme",
              "Richtung γ_M > γ_S aus Kopplungsargument (Kap. 2.1)", "betrieb"),
    Uncertain("gamma_S", "Wartungsexponent Microservices",
              0.20, 0.35, 0.50, "–", "gesetzt", "Annahme", "", "betrieb"),
    # Infrastruktur
    Uncertain("F_M", "Infrastruktur-Fixkosten Monolith p. a.",
              6_000, 12_000, 20_000, "EUR/a", "gesetzt", "Annahme", "", "betrieb"),
    Uncertain("Phi", "Plattform-Grundlast Microservices p. a. (Werkzeuge, Betrieb)",
              20_000, 40_000, 80_000, "EUR/a", "gesetzt",
              r"Annahme; Richtung: \textcite[S.~27]{taibi2017}",
              "keine begutachteten Zahlenwerte; Varianten Φ niedrig/hoch", "betrieb"),
    Uncertain("V", "lastabhängige Infrastrukturkosten Monolith p. a. bei N0",
              20_000, 30_000, 45_000, "EUR/a", "gesetzt", "Annahme", "", "betrieb"),
    Uncertain("psi", "relative Abweichung lastabhängiger Infrastrukturkosten Microservices",
              -0.15, 0.00, 0.50, "–", "relation_belegt",
              r"\textcite[S.~182]{villamizar2016}; \textcite[S.~20364--20365]{blinowski2022}",
              "−13,4 % (Villamizar) bis Durchsatznachteil Faktor 1,37 bis > 2 (Blinowski); Modus 0", "betrieb"),
    Uncertain("beta_M", "Infrastrukturexponent Monolith",
              0.90, 1.10, 1.40, "–", "relation_belegt",
              r"\textcite[S.~20360, 20369]{blinowski2022}",
              "Kosten steigen jenseits bestimmter Konfigurationen stark; Scale-up teils effizient", "betrieb"),
    Uncertain("beta_S", "Infrastrukturexponent Microservices",
              0.85, 0.95, 1.05, "–", "relation_belegt",
              r"\textcite[S.~20365]{blinowski2022}",
              "Durchsatz steigt annähernd linear mit Instanzen", "betrieb"),
    Uncertain("s", "Kapazitätsstufe Microservices je Nutzerverdopplung",
              5_000, 20_000, 50_000, "EUR", "gesetzt", "Annahme", "", "betrieb"),
    # Kapazität und Migration
    Uncertain("h", "Kapazitätsreserve des Monolithen (Kapazitätsgrenze / N0)",
              2.0, 5.0, 20.0, "–", "gesetzt", "Annahme",
              "Existenz einer Grenze: Villamizar S. 180, Blinowski S. 20360; Höhe gesetzt", "kapazitaet_migration"),
    Uncertain("mu", "Migrationskosten (Vielfaches von I_M)",
              0.50, 1.00, 2.00, "–", "gesetzt", "Annahme",
              "Fallwerte (Gouigoux & Tamzalit 2017; Fritzsch et al. 2019, S. 486) nicht übertragbar", "kapazitaet_migration"),
    Uncertain("d", "Migrationsdauer",
              1.5, 2.0, 4.0, "Jahre", "hergeleitet",
              r"\textcite[S.~484, 487]{fritzsch2019}",
              "1,5 bis über 3 Jahre; laufende Migrationen bis 4 Jahre erwartet", "kapazitaet_migration"),
]

UNCERTAIN_BY_SYMBOL = {u.symbol: u for u in UNCERTAIN}


def modes() -> dict:
    """Modalwerte aller unsicheren Parameter (Basisfall)."""
    return {u.symbol: u.mode for u in UNCERTAIN}
