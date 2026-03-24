import os
import sys
from importlib import import_module
from pathlib import Path

import numpy as np


TARGET_SOURCE_FOLDER = os.environ.get("SMOKE_TEST_SOURCE_FOLDER", "robot")
TARGET_DIR = Path(os.environ.get("SMOKE_TEST_TARGET_DIR", ".")).resolve()
ROOT = TARGET_DIR / TARGET_SOURCE_FOLDER
if not ROOT.exists():
    raise FileNotFoundError(
        f"Smoke test source folder does not exist: {ROOT} "
        "(set SMOKE_TEST_TARGET_DIR and/or SMOKE_TEST_SOURCE_FOLDER)"
    )
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def run_smoke_check() -> None:
    poses_module = import_module("common.poses")
    boundary_module = import_module("observation_models.boundary")
    Poses = poses_module.Poses
    BoundaryObservationModel = boundary_module.BoundaryObservationModel

    poses = Poses.generate(1000, (0, 1500), (0, 1500), (0, 2 * np.pi))
    model = BoundaryObservationModel()
    weights = model.calculate_weights(poses)

    assert weights.shape == (1000,), "Expected one weight per pose"
    assert np.isfinite(weights).all(), "Weights must be finite"

    min_weight = float(weights.min())
    max_weight = float(weights.max())
    assert min_weight >= 0.0, "Weights must be non-negative"
    assert max_weight <= 1.0, "Weights must be <= 1"

    assert poses.positions.shape == (1000, 2), "positions shape mismatch"

    print("smoke_poses_and_boundary: PASS")
    print(f"weights min/max: {min_weight:.6f}/{max_weight:.6f}")
    print(f"target dir: {TARGET_DIR}")
    print(f"source folder: {TARGET_SOURCE_FOLDER}")


if __name__ == "__main__":
    run_smoke_check()
