"""Tests für die plattformunabhängige Replikationsprüfung (src/verify.py)."""

import numpy as np
import pandas as pd

from src.verify import TOL, Comparison, check_published


def compare(ref, new):
    c = Comparison()
    c.value("x", ref, new)
    return c


def test_published_data_match_checksums():
    assert check_published() == []


def test_last_digit_differences_are_accepted():
    ref = {"a": [0.1234567890123456, -0.8885524231820752], "n": 10000, "s": "EV"}
    new = {"a": [0.1234567890123457, -0.8885524231820754], "n": 10000, "s": "EV"}
    c = compare(ref, new)
    assert c.errors == []
    assert 0 < c.max_rel < 1e-14


def test_deviation_above_tolerance_is_reported():
    c = compare({"a": 1.0}, {"a": 1.0 + 10 * TOL})
    assert len(c.errors) == 1


def test_integers_strings_and_booleans_must_match_exactly():
    assert compare({"n": 3}, {"n": 4}).errors
    assert compare({"s": "EV"}, {"s": "ev"}).errors
    assert compare({"b": True}, {"b": False}).errors


def test_structure_changes_are_reported():
    assert compare({"a": 1}, {"b": 1}).errors
    assert compare([1.0, 2.0], [1.0]).errors


def test_dataframes_compare_numbers_with_tolerance_and_text_exactly():
    ref = pd.DataFrame({"param": ["h", "mu"], "wert": [0.5, 1e-300], "rang": [1, 2]})
    near = pd.DataFrame({"param": ["h", "mu"], "wert": [0.5 * (1 + 1e-13), 0.0], "rang": [1, 2]})
    assert compare(ref, near).errors == []
    other_text = near.assign(param=["h", "d"])
    assert compare(ref, other_text).errors


def test_arrays_and_missing_values():
    a = np.array([1.0, np.nan, 3.0])
    assert compare(a, a.copy()).errors == []
    assert compare(a, np.array([1.0, 2.0, 3.0])).errors
    assert compare(np.array([1, 2]), np.array([1, 3])).errors


def test_rounding_noise_around_zero_is_accepted():
    # Tornado-Spannweite eines Parameters ohne Einfluss: mathematisch 0, gespeichert als Rundungsrest
    assert compare({"spannweite": 5.820766091346741e-11}, {"spannweite": 2.9103830456733704e-11}).errors == []


def test_real_deviation_in_small_values_is_reported():
    # Anteile und Wahrscheinlichkeiten liegen unter 1: 1e-6 ist dort eine echte Abweichung
    assert compare({"anteil": 0.4213}, {"anteil": 0.4213 + 1e-6}).errors
