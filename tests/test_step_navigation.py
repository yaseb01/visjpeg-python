"""
Regression-Test fuer die Schritt-Navigation (Radio + Weiter/Zurueck).

Stellt sicher, dass jeder Wechsel mit EINEM Klick funktioniert. Hintergrund:
Ein keyless st.radio mit wechselndem index= bekommt bei jedem Schrittwechsel
eine neue Widget-ID (index fliesst in die Identitaet ein) – im echten Browser
mussten Klicks deshalb teils doppelt erfolgen. Das Radio nutzt jetzt einen
stabilen key und wird ausschliesslich ueber den Session-State gesteuert.

Benoetigt streamlit (+ plotly, matplotlib); wird sonst uebersprungen.
"""

import pytest

streamlit = pytest.importorskip("streamlit", reason="streamlit nicht installiert")
plotly = pytest.importorskip("plotly", reason="plotly nicht installiert")
matplotlib = pytest.importorskip("matplotlib", reason="matplotlib nicht installiert")

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from streamlit.testing.v1 import AppTest

APP_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "visjpeg", "streamlit_app.py"
)

STEPS = [
    "Uebersicht",
    "1. Farbraum",
    "2. DCT",
    "3. Quantisierung",
    "4. Zick-Zack",
    "5. DPCM + RLE",
    "6. Entropie",
]


def _fresh_app():
    at = AppTest.from_file(APP_PATH, default_timeout=120)
    at.run()
    assert not at.exception, str(at.exception)
    return at


def _button(at, label_part):
    return next(b for b in at.button if label_part in b.label)


def _check(at, expected, context):
    assert not at.exception, f"{context}: {at.exception}"
    assert at.radio[0].value == expected, (
        f"{context}: radio={at.radio[0].value!r}, erwartet {expected!r}"
    )


def test_weiter_single_click_walks_all_steps():
    at = _fresh_app()
    for i in range(1, len(STEPS)):
        _button(at, "Weiter").click()
        at.run()
        _check(at, STEPS[i], f"Weiter #{i}")


def test_zurueck_single_click_walks_back():
    at = _fresh_app()
    at.radio[0].set_value(STEPS[-1])
    at.run()
    for i in range(len(STEPS) - 2, -1, -1):
        _button(at, "Zurueck").click()
        at.run()
        _check(at, STEPS[i], f"Zurueck #{i}")


def test_radio_switches_with_single_click():
    at = _fresh_app()
    for target in ["4. Zick-Zack", "6. Entropie", "1. Farbraum", "Uebersicht"]:
        at.radio[0].set_value(target)
        at.run()
        _check(at, target, f"Radio -> {target}")


def test_mixed_radio_and_buttons():
    at = _fresh_app()
    at.radio[0].set_value("5. DPCM + RLE")
    at.run()
    _check(at, "5. DPCM + RLE", "mix: radio 5")
    _button(at, "Weiter").click()
    at.run()
    _check(at, "6. Entropie", "mix: Weiter")
    _button(at, "Zurueck").click()
    at.run()
    _check(at, "5. DPCM + RLE", "mix: Zurueck")


def test_buttons_disabled_at_bounds():
    at = _fresh_app()
    assert _button(at, "Zurueck").disabled, "Zurueck muss am Anfang disabled sein"
    assert not _button(at, "Weiter").disabled, "Weiter muss am Anfang aktiv sein"
    at.radio[0].set_value(STEPS[-1])
    at.run()
    assert _button(at, "Weiter").disabled, "Weiter muss am Ende disabled sein"
    assert not _button(at, "Zurueck").disabled, "Zurueck muss am Ende aktiv sein"
