<div align="center">

# Microservices oder Monolith first?

**Stochastisches Kostenmodell zur Amortisation von Microservices-Architekturen unter Wachstumsunsicherheit**

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22983244.svg)](https://doi.org/10.5281/zenodo.22983244)
[![Tests](https://github.com/jonasyr/microservices-amortization-model/actions/workflows/tests.yml/badge.svg)](https://github.com/jonasyr/microservices-amortization-model/actions/workflows/tests.yml)
[![Python 3.14](https://img.shields.io/badge/Python-3.14-184f95?logo=python&logoColor=white)](https://www.python.org/)
[![Lizenz: MIT](https://img.shields.io/badge/Lizenz-MIT-184f95)](LICENSE)
[![Reproduzierbar: fester Seed](https://img.shields.io/badge/reproduzierbar-fester%20Seed-184f95)](#exakte-replikation)

Begleitcode zur Projektarbeit<br>
*„Amortisation von Microservices-Architekturen unter Wachstumsunsicherheit:
Ein stochastisches Kostenmodell im Vergleich zu einem Monolith-first-Vorgehen“*

Jonas Weirauch · IU Internationale Hochschule · B.Sc. Informatik · 2026

</div>

<br>

| | |
|---|---|
| **Kurs** | Praxisprojekt 6 (Kurscode DSPRAXP6042501) |
| **Prüfungsform** | Projektarbeit |
| **Forschungsfrage** | Unter welchen Wachstums- und Kostenbedingungen amortisiert sich die Mehrinvestition in eine Microservices-Architektur innerhalb von fünf Jahren? |
| **Methode** | Monte-Carlo-Simulation, 10 000 Parametersätze, Barwert in Monatsschritten, Horizont 5 Jahre |

## Inhalt

- [Worum es geht](#worum-es-geht)
- [Kernergebnisse](#kernergebnisse)
- [Exakte Replikation](#exakte-replikation)
- [Struktur](#struktur)
- [Zitieren](#zitieren)
- [English summary](#english-summary)

## Worum es geht

Lohnt es sich, eine neue Plattform von Beginn an als Microservices-Architektur zu bauen, oder ist
es günstiger, mit einem Monolithen zu starten und erst zu migrieren, wenn die Last es verlangt?
Das Modell vergleicht die barwertigen architekturbedingten Kosten beider Vorgehensweisen:

- **Microservices von Beginn (MS):** höhere Anfangsinvestition, Wartungs- und Plattformkosten,
  dafür Skalierung in Kapazitätsstufen.
- **Monolith first mit Migrationsoption (MF):** günstiger Start; erreicht die Nutzerzahl die
  Kapazitätsgrenze des Monolithen, folgt eine Migration mit Parallelbetrieb.

Fünfzehn unsichere Kostenparameter werden aus Beta-PERT-Verteilungen gezogen. Die
Parameterbereiche und ihre Quellen stehen in [`src/params.py`](src/params.py).

## Kernergebnisse

Basisfall, 10 000 Parametersätze. Einordnung, Grenzen und alle Varianten stehen in der Arbeit.

| Kennzahl | Ergebnis |
|---|---|
| Szenariogewichtet (5 / 20 / 60 % Wachstum, p = 0,3 / 0,5 / 0,2): MF günstiger | in 99,93 % der Parametersätze |
| Starkes Wachstum (60 % p. a.): MS günstiger | 65,7 % (95-%-Intervall 64,8–66,6 %) |
| Break-even-Wachstumsrate *g\** (Amortisationswahrscheinlichkeit 50 %) | ≈ 55 % p. a. (Übergangsbereich 44–66 %) |
| *g\** über alle Modell- und Parametervarianten | ≈ 32–65 % p. a. |
| *g\** bei zehn Jahren Horizont | ≈ 24 % p. a. |
| Einflussreichste Größen (Varianzanteil) | Plattform-Grundlast, Kapazitätsreserve, Wartungsmehraufwand, Infrastrukturkosten |

<p align="center">
  <img src="output/figures/abb_wachstumskurve.png" width="820"
       alt="Zwei Diagramme über der jährlichen Wachstumsrate von 0 bis 100 Prozent. Oben: Der Anteil der Parametersätze, in denen Microservices günstiger sind, bleibt bis etwa 30 Prozent Wachstum nahe null, steigt dann steil an und erreicht 50 Prozent bei 54,7 Prozent Wachstum. Unten: Median und 90-Prozent-Intervall der Kostendifferenz, die mit dem Wachstum von etwa minus 360 auf plus 700 Tausend Euro steigt und bei g* die Nulllinie kreuzt.">
</p>
<p align="center"><sub><b>Abb. 1</b> Amortisation in Abhängigkeit von der Wachstumsrate: (a) Anteil der Parametersätze mit Kostenvorteil für Microservices, (b) Median und 90-%-Intervall der Kostendifferenz ΔK = K<sub>MF</sub> − K<sub>MS</sub>.</sub></p>

<p align="center">
  <img src="output/figures/abb_heatmap.png" width="820"
       alt="Heatmap mit der Wachstumsrate auf der x-Achse und der Kapazitätsreserve des Monolithen (2- bis 20-fache Ausgangslast) auf der y-Achse. Dunklere Felder bedeuten einen höheren Anteil mit Kostenvorteil für Microservices. Die 50-Prozent-Linie verschiebt sich mit größerer Kapazitätsreserve von etwa 23 zu etwa 69 Prozent Wachstum.">
</p>
<p align="center"><sub><b>Abb. 2</b> Anteil der Parametersätze mit Kostenvorteil für Microservices nach Wachstumsrate und Kapazitätsreserve; Isolinien bei 20, 50 und 80 %.</sub></p>

## Exakte Replikation

Alle Zufallszahlen stammen aus einem festen Startwert (`SEED` in
[`src/params.py`](src/params.py)); alle Pakete sind in [`requirements.txt`](requirements.txt)
gepinnt. Ein frischer Lauf erzeugt die Ergebnisdaten **byte-identisch** zum veröffentlichten Stand.

```bash
git clone https://github.com/jonasyr/microservices-amortization-model.git
cd microservices-amortization-model
python3.14 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python -m src.run_all     # vollständiger Lauf, ca. 4–5 min → output/data/
sha256sum -c SHA256SUMS   # prüft alle Ergebnisdateien gegen den veröffentlichten Stand
python -m src.figures     # Abbildungen → output/figures/
python -m src.tables      # LaTeX-Tabellen und Zahlenmakros der Arbeit → output/tabellen/
pytest                    # Grenzfall- und Regressionstests
```

Referenzumgebung: Linux x86_64, Python 3.14.7. Die Replikation lässt sich auch ohne eigene
Installation prüfen: Unter *Actions → Reproduktion → Run workflow* rechnet GitHub den
vollständigen Lauf und vergleicht die Prüfsummen.

## Struktur

| Pfad | Inhalt |
|---|---|
| [`src/params.py`](src/params.py) | Konstanten, Szenarien, unsichere Parameter mit Herkunft und Beleg |
| [`src/model.py`](src/model.py) | Kostenfunktionen und Barwerte beider Alternativen |
| [`src/sampling.py`](src/sampling.py) | Ziehung der Parametersätze (Beta-PERT, gleichverteilt) |
| [`src/experiments.py`](src/experiments.py) | Szenarien, Break-even, Heatmap, Sensitivität, Varianten |
| [`src/analysis.py`](src/analysis.py) | PRCC, SRRC, Hilfsfunktionen |
| [`src/run_all.py`](src/run_all.py) | vollständiger Lauf, schreibt `output/data/` |
| [`src/figures.py`](src/figures.py), [`src/tables.py`](src/tables.py) | Abbildungen und LaTeX-Tabellen aus den Ergebnisdaten |
| [`tests/`](tests/) | Grenzfall- und Regressionstests (`pytest`) |
| [`output/data/`](output/data/) | Ergebnisdaten des veröffentlichten Laufs (CSV/JSON) |
| [`SHA256SUMS`](SHA256SUMS) | Prüfsummen der Ergebnisdaten |

## Zitieren

Weirauch, J. (2026). *Stochastisches Kostenmodell: Microservices von Beginn vs. Monolith first
mit Migrationsoption* [Software]. Zenodo. https://doi.org/10.5281/zenodo.22983244

Die DOI steht für alle Versionen und führt immer zur neuesten. Für eine bestimmte Version die
Versions-DOI von der [Zenodo-Seite](https://doi.org/10.5281/zenodo.22983244) verwenden.
Maschinenlesbare Angaben: [`CITATION.cff`](CITATION.cff); GitHub zeigt dazu rechts
„Cite this repository“ an.

## English summary

Stochastic total-cost model comparing *microservices from the start* with *monolith first with a
migration option* under uncertain user growth (Monte Carlo with 10,000 parameter sets, discounted,
monthly steps, five-year horizon). It computes break-even growth rates, a growth × capacity-reserve
map, local and global sensitivity (tornado, PRCC, SRRC²) and model variants. A fresh run
reproduces all result files byte for byte (`sha256sum -c SHA256SUMS`). Companion code to a project
thesis in the B.Sc. Computer Science programme at IU International University of Applied Sciences
(course “Praxisprojekt 6”, DSPRAXP6042501).

## Lizenz

[MIT](LICENSE) © 2026 Jonas Weirauch · Änderungen: [CHANGELOG.md](CHANGELOG.md)
