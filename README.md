# Stochastisches Kostenmodell: Microservices von Beginn vs. Monolith first

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22983244.svg)](https://doi.org/10.5281/zenodo.22983244)
[![Lizenz: MIT](https://img.shields.io/badge/Lizenz-MIT-blue.svg)](LICENSE)

Begleitcode zur Projektarbeit **„Amortisation von Microservices-Architekturen unter
Wachstumsunsicherheit: Ein stochastisches Kostenmodell im Vergleich zu einem
Monolith-first-Vorgehen“**.

| | |
|---|---|
| Hochschule | IU Internationale Hochschule |
| Studiengang | Informatik (B.Sc.) |
| Kurs | Praxisprojekt 6 (Kurscode DSPRAXP6042501) |
| Prüfungsform | Projektarbeit |
| Autor | Jonas Weirauch |
| Jahr | 2026 |

## Worum es geht

Lohnt es sich, eine neue Plattform von Beginn an als Microservices-Architektur zu bauen, oder
ist es günstiger, mit einem Monolithen zu starten und erst zu migrieren, wenn die Last es
verlangt? Das Modell vergleicht über einen Horizont von fünf Jahren die barwertigen
architekturbedingten Kosten beider Vorgehensweisen:

- **Microservices von Beginn (MS):** höhere Anfangsinvestition und Betriebskosten, dafür
  Skalierung in Kapazitätsstufen.
- **Monolith first mit Migrationsoption (MF):** günstiger Start; erreicht die Nutzerzahl die
  Kapazitätsgrenze des Monolithen, folgt eine Migration mit Parallelbetrieb.

Fünfzehn unsichere Kostenparameter werden aus Beta-PERT-Verteilungen gezogen (10 000
Parametersätze, fester Startwert). Ausgewertet werden Szenarien, Break-even-Wachstumsraten,
eine Kreuztabelle aus Wachstum und Kapazitätsreserve, lokale und globale Sensitivität
(Tornado, PRCC, SRRC²) sowie Modellvarianten. Parameterbereiche und ihre Quellen stehen in
`src/params.py`.

## English summary

Stochastic total-cost model comparing *microservices from the start* with *monolith first with a
migration option* under uncertain user growth (Monte Carlo, discounted, monthly steps,
five-year horizon). It computes break-even growth rates, a growth × capacity-reserve map, local
and global sensitivity (tornado, PRCC, SRRC²) and model variants. Fully reproducible with a fixed
seed. Companion code to a project thesis (B.Sc. Computer Science, IU International University of
Applied Sciences, course “Praxisprojekt 6”, DSPRAXP6042501).

## Struktur

| Pfad | Inhalt |
|---|---|
| `src/params.py` | Konstanten, Szenarien, unsichere Parameter mit Herkunft und Beleg |
| `src/model.py` | Kostenfunktionen und Barwerte beider Alternativen |
| `src/sampling.py` | Ziehung der Parametersätze (Beta-PERT, gleichverteilt) |
| `src/experiments.py` | Szenarien, Break-even, Heatmap, Sensitivität, Varianten |
| `src/analysis.py` | PRCC, SRRC, Hilfsfunktionen |
| `src/run_all.py` | vollständiger Lauf, schreibt `output/data/` |
| `src/figures.py`, `src/tables.py` | Abbildungen und LaTeX-Tabellen aus den Ergebnisdaten |
| `tests/` | Grenzfall- und Regressionstests (`pytest`) |
| `output/data/` | Ergebnisdaten des veröffentlichten Laufs (CSV/JSON) |

## Ausführen

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m src.run_all     # ca. 5 min, schreibt output/data/
python -m src.figures     # output/figures/
python -m src.tables      # output/tabellen/
pytest
```

Getestet mit Python 3.14 und den Paketversionen in `requirements.txt`. Alle Ergebnisse sind
durch den festen Startwert reproduzierbar; die Abbildungen werden byte-identisch erzeugt.

## Zitieren

Weirauch, J. (2026). *Stochastisches Kostenmodell: Microservices von Beginn vs. Monolith first
mit Migrationsoption* [Software]. Zenodo. https://doi.org/10.5281/zenodo.22983244

Die DOI oben steht für alle Versionen. Für eine bestimmte Version bitte die Versions-DOI von der
Zenodo-Seite verwenden. Maschinenlesbare Angaben: `CITATION.cff`.

## Lizenz

MIT, siehe `LICENSE`.
