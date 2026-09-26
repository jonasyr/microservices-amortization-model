# Changelog

Alle nennenswerten Änderungen. Versionen folgen [Semantic Versioning](https://semver.org/lang/de/).

## [1.0.1] – 2026-09-27

Modelllogik und alle Ergebniswerte sind unverändert; geändert haben sich Dokumentation,
Metadaten und die Art, wie Ergebnisse gespeichert werden.

- Deterministische Ausgabe: Python-Version, Plattform und Laufzeit stehen nicht mehr in
  `results.json`, sondern in `output/data/lauf.json` (nicht versioniert); `ziehungen.csv.gz` wird
  ohne Zeitstempel geschrieben. Dadurch sind alle Ergebnisdateien über Läufe und Rechner hinweg
  byte-identisch und per `SHA256SUMS` prüfbar.
- README mit Kernergebnissen, Abbildungen und Anleitung zur exakten Replikation
- Kurs- und Hochschulangaben in `CITATION.cff` und `.zenodo.json`
- `SHA256SUMS` für die Ergebnisdaten, GitHub-Actions-Workflows für Tests und Replikation

## [1.0.0] – 2026-09-26

- Erste veröffentlichte Fassung, Grundlage der Projektarbeit
