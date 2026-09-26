# Kostenmodell Monolith vs. Microservices

Stochastisches Kostenmodell (Monte-Carlo) zur Projektarbeit
„Unter welchen Wachstums- und Kostenbedingungen amortisiert sich die Mehrinvestition
in eine Microservices-Architektur innerhalb von fünf Jahren?"

Eigenständig lauffähig; vorgesehen zur späteren Auslagerung als eigenes Repository
mit archivierter Version (DOI).

## Struktur

| Pfad | Inhalt |
|---|---|
| `src/` | Modellcode (Parameter, Kostenfunktionen, Simulation, Auswertung, Abbildungen) |
| `tests/` | Plausibilitäts- und Regressionstests (`pytest`) |
| `output/data/` | Ergebnisdaten (CSV/JSON) — Quelle aller Zahlen im Text |
| `output/figures/` | Abbildungen; finale Versionen werden nach `../figures/` exportiert |
| `requirements.txt` | gepinnte Paketversionen |

## Ausführen

```bash
cd model
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m src.run_all      # rechnet alles, schreibt output/ und ../figures/
pytest
```

Zufallszahlen: fester Seed (in `src/params.py`), damit alle Ergebnisse reproduzierbar sind.
