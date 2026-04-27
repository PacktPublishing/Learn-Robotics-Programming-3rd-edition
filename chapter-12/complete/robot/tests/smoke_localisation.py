"""Smoke test for localisation.py.

The module runs ``service = Localisation(); service.start()`` at import time.
``start()`` connects to MQTT and then enters ``while True: time.sleep(0.1)``,
so a plain ``import localisation`` would block forever (or error without a
broker).

Strategy
--------
* Use ``importlib.util.spec_from_file_location`` + ``exec_module`` on a fresh
  ``types.ModuleType`` object so the module code runs in an isolated namespace.
* Patch ``common.mqtt_behavior.connect`` (the ``from … import connect`` in
  localisation.py picks up the patch because it runs inside the ``with`` block).
* Patch ``time.sleep`` to raise ``SystemExit`` – this breaks the ``while True``
  loop cleanly.  All definitions made before ``start()`` blocks are preserved
  in the module namespace.
* Use a small population (TEST_POPULATION) for speed in the test instances.
"""

import importlib.util
import json
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TEST_POPULATION = 500


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_module():
    """Load localisation.py into an isolated module object.

    ``connect`` is patched so no real MQTT connection is attempted.
    ``time.sleep`` is patched to raise ``SystemExit``, which terminates the
    ``while True`` loop in ``start()`` and is caught here.
    """
    loc_path = ROOT / "localisation.py"
    spec = importlib.util.spec_from_file_location("localisation_smoke", str(loc_path))
    loc_mod = types.ModuleType("localisation_smoke")
    loc_mod.__spec__ = spec
    loc_mod.__file__ = str(loc_path)

    mock_client = MagicMock()

    with patch("common.mqtt_behavior.connect", return_value=mock_client), \
         patch("time.sleep", side_effect=SystemExit("break_loop")):
        try:
            spec.loader.exec_module(loc_mod)
        except SystemExit:
            pass  # Expected – raised by patched time.sleep to exit the loop.

    assert hasattr(loc_mod, "Localisation"), \
        "Localisation class was not defined before the loop started"
    return loc_mod


def _make_localisation(loc_mod):
    """Return a Localisation instance using a small population for speed."""
    loc_mod.population_size = TEST_POPULATION
    loc_mod.ess_threshold = TEST_POPULATION // 2
    return loc_mod.Localisation()


# ---------------------------------------------------------------------------
# Smoke checks
# ---------------------------------------------------------------------------

def test_import():
    loc = _load_module()
    print("test_import: PASS")
    return loc


def test_instantiation(loc):
    instance = _make_localisation(loc)
    assert instance is not None
    assert instance.poses is not None
    assert instance.wheel_distance == 136
    print("test_instantiation: PASS")
    return instance


def test_convert_encoders_straight(instance):
    """Equal wheel deltas => straight line, zero rotation."""
    trans, rot = instance.convert_encoders_to_motion(100, 100)
    assert trans == 100, f"Expected translation 100, got {trans}"
    assert rot == 0, f"Expected rotation 0, got {rot}"
    print("test_convert_encoders_straight: PASS")


def test_convert_encoders_turn(instance):
    """Unequal wheel deltas => non-zero translation and rotation."""
    trans, theta = instance.convert_encoders_to_motion(50, 150)
    expected_mid = 100.0
    expected_theta = (150 - 50) / instance.wheel_distance
    assert abs(trans - expected_mid) < 1e-9, f"translation mismatch: {trans}"
    assert abs(theta - expected_theta) < 1e-9, f"theta mismatch: {theta}"
    print("test_convert_encoders_turn: PASS")


def test_randomise_motion(instance):
    """randomise_motion should return two arrays matching the population size."""
    n = len(instance.poses)
    trans_s, rot_s = instance.randomise_motion(100.0, 0.5)
    assert trans_s.shape == (n,), f"trans_samples shape mismatch: {trans_s.shape}"
    assert rot_s.shape == (n,), f"rot_samples shape mismatch: {rot_s.shape}"
    assert np.isfinite(trans_s).all(), "trans_samples contains non-finite values"
    assert np.isfinite(rot_s).all(), "rot_samples contains non-finite values"
    print(f"test_randomise_motion: PASS  (population={n})")


def test_calculate_ess(instance):
    """ESS with uniform weights should equal the population size."""
    n = len(instance.poses)
    ess = instance.calculate_ess()
    # Uniform weights => ESS == population_size (within floating-point tolerance)
    assert abs(ess - n) < 1.0, f"ESS {ess:.1f} unexpectedly far from {n}"
    print(f"test_calculate_ess: PASS  (ESS={ess:.1f}, pop={n})")


def test_apply_observational_models(instance):
    """apply_observational_models should return one finite weight per pose."""
    n = len(instance.poses)
    weights = instance.apply_observational_models()
    assert weights.shape == (n,), f"weights shape mismatch: {weights.shape}"
    assert np.isfinite(weights).all(), "weights contain non-finite values"
    assert (weights >= 0).all(), "weights contain negative values"
    print(f"test_apply_observational_models: PASS  (min={weights.min():.6f}, max={weights.max():.6f})")


def test_on_encoders_data(instance):
    """on_encoders_data should run without exceptions with a mock MQTT message."""
    mock_client = MagicMock()
    mock_msg = MagicMock()
    mock_msg.payload = json.dumps({
        "left_distance": 110,
        "right_distance": 120,
    }).encode()

    instance.on_encoders_data(mock_client, None, mock_msg)

    assert instance.previous_left_distance == 110
    assert instance.previous_right_distance == 120
    assert np.isclose(np.sum(instance.weights), 1.0), "weights should stay normalized"
    print("test_on_encoders_data: PASS")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_smoke_check():
    loc = test_import()
    instance = test_instantiation(loc)
    test_convert_encoders_straight(instance)
    test_convert_encoders_turn(instance)
    test_randomise_motion(instance)
    test_calculate_ess(instance)
    test_apply_observational_models(instance)
    test_on_encoders_data(instance)
    print("\nsmoke_localisation: ALL PASS")


if __name__ == "__main__":
    run_smoke_check()
