# Stochastisches Kostenmodell: Microservices von Beginn vs. Monolith first

Monte-Carlo-Kostenmodell zur Projektarbeit
„Amortisation von Microservices-Architekturen unter Wachstumsunsicherheit“
(IU Internationale Hochschule, B.Sc. Informatik, 2026).

Das Modell vergleicht über einen Horizont von fünf Jahren die barwertigen Kosten zweier
Vorgehensweisen: **Microservices von Beginn** (MS) und **Monolith first mit Migrationsoption**
(MF), bei der der Monolith beim Erreichen seiner Kapazitätsgrenze migriert wird. Fünfzehn
unsichere Kostenparameter werden aus Beta-PERT-Verteilungen gezogen (10 000 Parametersätze,
fester Startwert). Die Parameterbereiche und ihre Quellen stehen in `src/params.py`.

*English summary:* stochastic total-cost model comparing "microservices from the start" with
"monolith first with a migration option" under uncertain user growth (Monte Carlo, discounted,
five-year horizon), including break-even growth rates, global sensitivity analysis (PRCC, SRRC²)
and model variants. Fully reproducible with a fixed seed.

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

Getestet mit Python 3.14 und den Paketversionen in `requirements.txt`.

## Zitieren

Siehe `CITATION.cff`. Lizenz: MIT (`LICENSE`).
