"""Prüft die Replikation auf jedem Betriebssystem.

1. Die veröffentlichten Ergebnisdaten in output/data/ stimmen mit SHA256SUMS überein.
2. Ein frischer vollständiger Lauf (fester Startwert) nach output/_verify/data/ stimmt mit den
   veröffentlichten Daten überein: Struktur, Texte und ganze Zahlen exakt, Gleitkommazahlen bis
   auf eine relative Abweichung von RTOL. Auf der Referenzplattform (Linux x86_64) sind die Dateien
   byte-identisch; andere Plattformen weichen höchstens in der letzten Stelle ab (Gleitkomma-
   bibliotheken).
3. Die Tabellen und Zahlenmakros der Arbeit, erzeugt aus beiden Datensätzen, sind exakt gleich.

Aufruf (aus dem Repo-Ordner):  python -m src.verify           # rechnet neu (ca. 6–8 min)
                                python -m src.verify --lauf DIR  # vergleicht einen vorhandenen Lauf
Exit-Code 0 = Replikation bestätigt, 1 = Abweichung.
"""

import argparse
import hashlib
import json
import math
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "output" / "data"
WORK = ROOT / "output" / "_verify"
SUMS = ROOT / "SHA256SUMS"
RTOL = 1e-9    # weit über den gemessenen Plattformabweichungen (Windows: 3e-13), weit unter jeder gedruckten Stelle
ATOL = 1e-12   # für Werte nahe null


def checksum_files() -> dict[str, str]:
    """Dateiname -> erwarteter SHA-256 aus SHA256SUMS (CRLF-tolerant)."""
    out = {}
    for line in SUMS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            digest, name = line.split(maxsplit=1)
            out[name.lstrip("*")] = digest.lower()
    return out


def check_published() -> list[str]:
    errors = []
    for name, digest in checksum_files().items():
        path = ROOT / name
        if not path.is_file():
            errors.append(f"fehlt: {name}")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            errors.append(f"Prüfsumme weicht ab: {name}")
    return errors


def load(path: Path):
    name = path.name
    if name.endswith((".csv", ".csv.gz")):
        return pd.read_csv(path)
    if name.endswith(".json"):
        return json.loads(path.read_text(encoding="utf-8"))
    if name.endswith(".npz"):
        with np.load(path, allow_pickle=False) as z:
            return {k: z[k] for k in z.files}
    raise ValueError(f"unbekanntes Format: {name}")


class Comparison:
    """Sammelt Abweichungen und die größte relative Abweichung von Gleitkommazahlen."""

    def __init__(self, rtol: float = RTOL, atol: float = ATOL):
        self.rtol, self.atol = rtol, atol
        self.errors: list[str] = []
        self.max_rel = 0.0

    def _numbers(self, where: str, a: np.ndarray, b: np.ndarray) -> None:
        a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
        if a.shape != b.shape:
            self.errors.append(f"{where}: Form {a.shape} statt {b.shape}")
            return
        same_nan = np.isnan(a) == np.isnan(b)
        if not same_nan.all():
            self.errors.append(f"{where}: fehlende Werte an anderer Stelle")
            return
        mask = ~np.isnan(a)
        a, b = a[mask], b[mask]
        if a.size == 0:
            return
        diff = np.abs(a - b)
        scale = np.maximum(np.abs(a), np.abs(b))
        rel = np.divide(diff, scale, out=np.zeros_like(diff), where=scale > 0)
        self.max_rel = max(self.max_rel, float(rel.max()))
        bad = diff > self.atol + self.rtol * scale
        if bad.any():
            self.errors.append(f"{where}: {int(bad.sum())} Werte außerhalb der Toleranz "
                               f"(größte relative Abweichung {float(rel.max()):.2e})")

    def value(self, where: str, ref, new) -> None:
        if isinstance(ref, pd.DataFrame):
            if list(ref.columns) != list(new.columns) or ref.shape != new.shape:
                self.errors.append(f"{where}: Spalten oder Form verschieden")
                return
            for col in ref.columns:
                r, n = ref[col], new[col]
                if pd.api.types.is_bool_dtype(r) or not pd.api.types.is_numeric_dtype(r):
                    if not r.astype(str).equals(n.astype(str)):
                        self.errors.append(f"{where}[{col}]: Werte verschieden")
                elif pd.api.types.is_integer_dtype(r) and pd.api.types.is_integer_dtype(n):
                    if not r.equals(n):
                        self.errors.append(f"{where}[{col}]: ganze Zahlen verschieden")
                else:
                    self._numbers(f"{where}[{col}]", r.to_numpy(), n.to_numpy())
        elif isinstance(ref, dict):
            if set(ref) != set(new):
                self.errors.append(f"{where}: Schlüssel verschieden")
                return
            for k in ref:
                self.value(f"{where}.{k}", ref[k], new[k])
        elif isinstance(ref, list):
            if not isinstance(new, list) or len(ref) != len(new):
                self.errors.append(f"{where}: Liste mit anderer Länge")
                return
            for i, (r, n) in enumerate(zip(ref, new)):
                self.value(f"{where}[{i}]", r, n)
        elif isinstance(ref, np.ndarray):
            if ref.dtype.kind in "biu" and new.dtype.kind in "biu":
                if not np.array_equal(ref, new):
                    self.errors.append(f"{where}: ganze Zahlen verschieden")
            else:
                self._numbers(where, ref, new)
        elif isinstance(ref, bool) or isinstance(new, bool) or ref is None or isinstance(ref, str):
            if ref != new:
                self.errors.append(f"{where}: {ref!r} statt {new!r}")
        elif isinstance(ref, int) and isinstance(new, int):
            if ref != new:
                self.errors.append(f"{where}: {ref} statt {new}")
        elif isinstance(ref, (int, float)) and isinstance(new, (int, float)):
            if math.isnan(ref) or math.isnan(new):
                if not (math.isnan(ref) and math.isnan(new)):
                    self.errors.append(f"{where}: fehlender Wert verschieden")
            else:
                self._numbers(where, np.array([ref]), np.array([new]))
        elif ref != new:
            self.errors.append(f"{where}: {ref!r} statt {new!r}")


def fresh_run(out: Path) -> None:
    from . import run_all
    run_all.DATA = out
    argv, sys.argv = sys.argv, ["run_all"]
    try:
        run_all.main()
    finally:
        sys.argv = argv


def build_tables(data: Path, out: Path) -> None:
    from . import tables
    tables.DATA, tables.TAB = data, out
    out.parent.mkdir(parents=True, exist_ok=True)
    tables.main()


def compare_tables(ref: Path, new: Path) -> list[str]:
    errors = []
    names = sorted(p.name for p in ref.iterdir())
    if names != sorted(p.name for p in new.iterdir()):
        return ["Tabellen: andere Dateien erzeugt"]
    for name in names:
        if (ref / name).read_bytes() != (new / name).read_bytes():
            errors.append(f"Tabelle weicht ab: {name}")
    return errors


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lauf", type=Path, help="vorhandenen Lauf (Ordner mit den Ergebnisdateien) vergleichen")
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):  # Windows-Konsole: Umlaute nie als Abbruchgrund
        sys.stdout.reconfigure(errors="replace")

    errors = check_published()
    if errors:
        print("Veröffentlichte Daten verändert, zuerst wiederherstellen (git checkout output/data):")
        print("\n".join(f"  {e}" for e in errors))
        return 1
    print(f"1/3 veröffentlichte Daten: {len(checksum_files())} Dateien stimmen mit SHA256SUMS überein")

    if WORK.exists():
        shutil.rmtree(WORK)
    run_dir = args.lauf
    if run_dir is None:
        run_dir = WORK / "data"
        print("2/3 frischer vollständiger Lauf nach output/_verify/data/ …")
        fresh_run(run_dir)

    cmp = Comparison()
    identical = 0
    for name in checksum_files():
        new_path = run_dir / Path(name).name
        if not new_path.is_file():
            cmp.errors.append(f"im Lauf fehlt: {Path(name).name}")
            continue
        if (ROOT / name).read_bytes() == new_path.read_bytes():
            identical += 1
            continue
        cmp.value(Path(name).name, load(ROOT / name), load(new_path))
    print(f"2/3 Ergebnisdaten: {identical} von {len(checksum_files())} byte-identisch, "
          f"größte relative Abweichung {cmp.max_rel:.1e} (Toleranz {RTOL:.0e})")

    build_tables(DATA, WORK / "tabellen_veroeffentlicht")
    build_tables(run_dir, WORK / "tabellen_lauf")
    table_errors = compare_tables(WORK / "tabellen_veroeffentlicht", WORK / "tabellen_lauf")
    n_tables = len(list((WORK / "tabellen_veroeffentlicht").iterdir()))
    print(f"3/3 Tabellen und Zahlen der Arbeit: {n_tables - len(table_errors)} von {n_tables} identisch")

    errors = cmp.errors + table_errors
    if errors:
        print("ABWEICHUNG:")
        print("\n".join(f"  {e}" for e in errors))
        return 1
    print("OK: Replikation bestätigt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
