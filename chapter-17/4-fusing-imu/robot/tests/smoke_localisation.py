"""Smoke test for localisation.py in chapter-17/4-fusing-imu.

Architecture notes
------------------
``localisation.py`` runs ``service = Localisation(); service.start()`` at
module level.  ``start()`` enters a ``while True: client.loop(0.2); ...``
loop.

Strategy
--------
* Patch ``common.mqtt_behavior.connect`` to return a ``MagicMock`` client.
* Set ``mock_client.loop.side_effect = SystemExit`` to break the while-loop.
* Change CWD to the chapter root for the duration of loading so that
  ``DistanceObservationModel`` can resolve its relative ``.npy`` path
  (``"robot/observation_models/distance_map.npy"``).
* Tests then exercise the classes (``EncoderMotionData``, ``ImuMotionData``,
  ``Localisation``) directly with a small population for speed.
"""

import importlib.util
import json
import os
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np

ROOT = Path(__file__).resolve().parents[1]  # chapter-17/4-fusing-imu/robot/
CHAPTER_DIR = ROOT.parent                   # chapter-17/4-fusing-imu/

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TEST_POPULATION = 500


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_module():
    """Load localisation.py into an isolated module object.

    ``connect`` is patched so no real MQTT connection is attempted.
    ``mock_client.loop`` raises ``SystemExit`` to break the while-loop.
    CWD is temporarily set to the chapter directory so that
    ``DistanceObservationModel`` can load its relative ``.npy`` file.
    """
    loc_path = ROOT / "localisation.py"
    spec = importlib.util.spec_from_file_location("localisation_smoke", str(loc_path))
    loc_mod = types.ModuleType("localisation_smoke")
    loc_mod.__spec__ = spec
    loc_mod.__file__ = str(loc_path)

    mock_client = MagicMock()
    mock_client.loop.side_effect = SystemExit("break_loop")

    original_cwd = os.getcwd()
    os.chdir(CHAPTER_DIR)
    try:
        import common.mqtt_behavior  # ensure it's in sys.modules so patch can resolve it
        with patch("common.mqtt_behavior.connect", return_value=mock_client):
            try:
                spec.loader.exec_module(loc_mod)
            except SystemExit:
                pass  # Expected – raised by mock_client.loop to exit the loop.
    finally:
        os.chdir(original_cwd)

    for cls_name in ("Localisation", "EncoderMotionData", "ImuMotionData"):
        assert hasattr(loc_mod, cls_name), \
            f"{cls_name} was not defined before the loop started"

    return loc_mod


def _make_localisation(loc_mod):
    """Return a Localisation instance with a small population for speed."""
    loc_mod.population_size = TEST_POPULATION
    loc_mod.ess_threshold = TEST_POPULATION // 2
    original_cwd = os.getcwd()
    os.chdir(CHAPTER_DIR)
    try:
        instance = loc_mod.Localisation()
    finally:
        os.chdir(original_cwd)
    return instance


# ---------------------------------------------------------------------------
# Smoke checks
# ---------------------------------------------------------------------------

def test_import():
    loc = _load_module()
    print("test_import: PASS")
    return loc


def test_encoder_motion_data(loc):
    """EncoderMotionData tracks encoder deltas and computes motion."""
    enc = loc.EncoderMotionData()
    assert enc.wheel_distance == 136

    mock_msg = MagicMock()

    # Straight line – equal deltas
    mock_msg.payload = json.dumps({"left_distance": 100, "right_distance": 100}).encode()
    enc.on_encoders_data(MagicMock(), None, mock_msg)
    trans, theta = enc.consume_data()
    assert trans == 100, f"Expected translation 100, got {trans}"
    assert theta == 0.0, f"Expected theta 0.0, got {theta}"

    # Turn – unequal deltas (previous positions are now 100/100)
    mock_msg.payload = json.dumps({"left_distance": 150, "right_distance": 250}).encode()
    enc.on_encoders_data(MagicMock(), None, mock_msg)
    trans2, theta2 = enc.consume_data()
    expected_trans = (50 + 150) / 2   # 100.0
    expected_theta = (150 - 50) / enc.wheel_distance
    assert abs(trans2 - expected_trans) < 1e-9, f"translation mismatch: {trans2}"
    assert abs(theta2 - expected_theta) < 1e-9, f"theta mismatch: {theta2}"

    # consume_data resets pending state
    trans3, theta3 = enc.consume_data()
    assert trans3 == 0.0 and theta3 == 0.0, "consume_data did not reset pending state"

    print("test_encoder_motion_data: PASS")


def test_imu_motion_data(loc):
    """ImuMotionData accumulates wrap-aware yaw deltas into pending_theta.
    The BNO055's internal NDOF Kalman fusion already handles sensor noise and
    vibration, so no additional LP filter is applied here."""
    imu = loc.ImuMotionData()
    assert imu.previous_yaw is None
    assert imu.pending_theta == 0.0

    # normalize_angle wraps to (-π, π]
    assert abs(imu.normalize_angle(0.0)) < 1e-9
    assert abs(imu.normalize_angle(2 * np.pi)) < 1e-9
    assert abs(imu.normalize_angle(np.pi + 0.1) - (-np.pi + 0.1)) < 1e-9

    mock_msg = MagicMock()

    # First on_imu_data: seeds previous_yaw, accumulates nothing
    mock_msg.payload = json.dumps({"yaw": 1.0}).encode()
    imu.on_imu_data(MagicMock(), None, mock_msg)
    assert abs(imu.previous_yaw - 1.0) < 1e-9
    assert imu.pending_theta == 0.0

    # Second reading: delta = normalize(1.5 - 1.0) = 0.5; pending_theta = 0.5
    mock_msg.payload = json.dumps({"yaw": 1.5}).encode()
    imu.on_imu_data(MagicMock(), None, mock_msg)
    assert abs(imu.pending_theta - 0.5) < 1e-9, \
        f"pending_theta mismatch: {imu.pending_theta}"

    # Third reading accumulates further
    mock_msg.payload = json.dumps({"yaw": 1.8}).encode()
    imu.on_imu_data(MagicMock(), None, mock_msg)
    assert abs(imu.pending_theta - 0.8) < 1e-9, \
        f"pending_theta mismatch after 3rd reading: {imu.pending_theta}"

    # consume_data returns accumulated delta and resets
    delta = imu.consume_data()
    assert abs(delta - 0.8) < 1e-9, f"consume_data mismatch: {delta}"
    assert imu.pending_theta == 0.0, "pending_theta not reset after consume"

    # --- Wrap-around cases ---
    # Helper: simulate two consecutive IMU readings and return the consumed delta.
    def _wrap_delta(from_yaw, to_yaw):
        imu_w = loc.ImuMotionData()
        msg = MagicMock()
        msg.payload = json.dumps({"yaw": from_yaw}).encode()
        imu_w.on_imu_data(MagicMock(), None, msg)  # seeds previous_yaw
        msg.payload = json.dumps({"yaw": to_yaw}).encode()
        imu_w.on_imu_data(MagicMock(), None, msg)
        return imu_w.consume_data()

    # 1. Just under 2π → just over 0  (small positive turn crossing 0/2π boundary)
    d = _wrap_delta(2 * np.pi - 0.05, 0.05)
    assert abs(d - 0.1) < 1e-9, f"0/2π crossing: expected 0.1, got {d:.6f}"

    # 2. Just over 0 → just under 2π  (small negative turn crossing 0/2π boundary)
    d = _wrap_delta(0.05, 2 * np.pi - 0.05)
    assert abs(d - (-0.1)) < 1e-9, f"2π/0 crossing: expected -0.1, got {d:.6f}"

    # 3. Just under +π → just over +π  (expressed as -(π-0.05) in wrapped coords)
    d = _wrap_delta(np.pi - 0.05, -(np.pi - 0.05))
    assert abs(d - 0.1) < 1e-9, f"+π crossing (under→over): expected 0.1, got {d:.6f}"

    # 4. Just over +π → just under +π  (small negative turn back across +π boundary)
    d = _wrap_delta(-(np.pi - 0.05), np.pi - 0.05)
    assert abs(d - (-0.1)) < 1e-9, f"+π crossing (over→under): expected -0.1, got {d:.6f}"

    # on_status_update subscribes to IMU euler topic when sys == 3 (fully calibrated)
    mock_client = MagicMock()
    mock_msg.payload = json.dumps({"sys": 3}).encode()
    imu.on_status_update(mock_client, None, mock_msg)
    mock_client.subscribe.assert_called_with("sensors/imu/euler")
    mock_client.message_callback_add.assert_called_once()

    # on_status_update does NOT subscribe when sys != 3
    mock_client2 = MagicMock()
    mock_msg.payload = json.dumps({"sys": 1}).encode()
    imu.on_status_update(mock_client2, None, mock_msg)
    mock_client2.subscribe.assert_not_called()

    print("test_imu_motion_data: PASS")


def test_instantiation(loc):
    instance = _make_localisation(loc)
    assert instance is not None
    assert instance.poses is not None
    assert len(instance.poses) == TEST_POPULATION
    assert isinstance(instance.encoder_data, loc.EncoderMotionData)
    assert isinstance(instance.imu_data, loc.ImuMotionData)
    assert instance.boundary_model is not None
    assert instance.distance_model is not None
    print("test_instantiation: PASS")
    return instance


def test_calculate_ess(instance):
    """ESS with uniform weights should equal the population size."""
    n = len(instance.poses)
    ess = instance.calculate_ess()
    assert abs(ess - n) < 1.0, f"ESS {ess:.1f} unexpectedly far from {n}"
    print(f"test_calculate_ess: PASS  (ESS={ess:.1f}, pop={n})")


def test_apply_observational_models(instance):
    """apply_observational_models should return one finite weight per pose."""
    n = len(instance.poses)
    weights = instance.apply_observational_models()
    assert weights.shape == (n,), f"weights shape mismatch: {weights.shape}"
    assert np.isfinite(weights).all(), "weights contain non-finite values"
    assert (weights >= 0).all(), "weights contain negative values"
    print(f"test_apply_observational_models: PASS  "
          f"(min={weights.min():.6f}, max={weights.max():.6f})")


def test_on_distance_readings(instance):
    """on_distance_readings processes an 8x8 JSON payload without error."""
    mock_msg = MagicMock()
    data = [500] * 64  # flat 8x8 grid of 500 mm readings
    mock_msg.payload = json.dumps(data).encode()
    instance.on_distance_readings(MagicMock(), None, mock_msg)
    assert instance.distance_model.relative_sensor_positions.shape == (8, 2)
    print("test_on_distance_readings: PASS")


def test_update(instance):
    """update() runs without raising; publishes poses and ESS."""
    mock_client = MagicMock()
    mock_msg = MagicMock()

    # Feed encoder data so motion is non-trivial
    mock_msg.payload = json.dumps({"left_distance": 50, "right_distance": 60}).encode()
    instance.encoder_data.on_encoders_data(mock_client, None, mock_msg)

    instance.update(mock_client)

    assert mock_client.publish.called
    print("test_update: PASS")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_smoke_check():
    loc = test_import()
    test_encoder_motion_data(loc)
    test_imu_motion_data(loc)
    instance = test_instantiation(loc)
    test_calculate_ess(instance)
    test_apply_observational_models(instance)
    test_on_distance_readings(instance)
    test_update(instance)
    print("\nsmoke_localisation: ALL PASS")


if __name__ == "__main__":
    run_smoke_check()
