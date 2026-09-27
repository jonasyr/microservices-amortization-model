# Changelog

Alle nennenswerten Änderungen. Versionen folgen [Semantic Versioning](https://semver.org/lang/de/).

## [1.1.1] (2026-09-27)

Modelllogik und alle Ergebniswerte sind unverändert (`SHA256SUMS` unverändert gültig). Geändert
haben sich Darstellung und Dokumentation.

- Tabellen: kaufmännische Rundung auf Basis der Dezimaldarstellung, Tab. 2 ohne unnötige
  Nachkommastellen und mit mehr Zeilenabstand, erklärte Symbole und Spaltenköpfe, H1 mit zwei
  Nachkommastellen, Konfidenzintervall der Monte-Carlo-Schätzung bei H2 ausdrücklich benannt,
  Zeichensetzung der Beschriftungen
- Neue Makros: Nulldurchgang von Mittelwert und Median von ΔK, Kostenzerlegung bei
  wahrscheinlichsten Werten, Anteil der Amortisation binnen zehn Jahren
- Abbildungen: einheitliche Begriffe (Parametersätze, Horizont, MS/MF), Varianzanteile einfarbig,
  Robustheit Teil d bis 150 %, kompaktere Höhen bei gleicher Schriftgröße
- Docstrings präzisiert (vorausschauender Auslöser, Amortisationsdauer)

## [1.1.0] (2026-09-27)

Modelllogik und alle Ergebniswerte aus 1.0.0 sind unverändert.

### Neu
- Amortisationsdauer je Parametersatz bei 60 % und 100 % Wachstum
  (`experiments.amortization_time`), zur Plausibilisierung gegen Praxisangaben
- Stabilität der Kernkennzahlen gegenüber dem Startwert mit fünf Startwerten
  (`experiments.seed_stability`)
- `SHA256SUMS` für alle Ergebnisdateien, GitHub-Actions-Workflows für Tests und Replikation,
  `pytest.ini` (Tests laufen mit `pytest` und `python -m pytest`) und `.python-version`

### Geändert
- Deterministische Ausgabe: Python-Version, Plattform und Laufzeit stehen nicht mehr in
  `results.json`, sondern in `output/data/lauf.json` (nicht versioniert). `ziehungen.csv.gz` wird
  ohne Zeitstempel geschrieben. Dadurch sind alle Ergebnisdateien über Läufe und Rechner hinweg
  byte-identisch.
- README mit Kernergebnissen, Abbildungen und Anleitung zur exakten Replikation
- Kurs-, Hochschul- und ORCID-Angaben in `CITATION.cff` und `.zenodo.json`

## [1.0.0] (2026-09-26)

- Erste veröffentlichte Fassung, Grundlage der Projektarbeit
