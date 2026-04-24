import sys
from importlib import import_module
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
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
    assert min_weight <= 0.01, "Outside-map particles should be strongly penalized"

    assert poses.positions.shape == (1000, 2), "positions shape mismatch"

    heading_test_poses = Poses([
        (1010.0, 490.0, 0.0),
        (1010.0, 490.0, np.pi / 4),
    ])
    heading_weights = model.calculate_weights(heading_test_poses)
    assert np.isclose(heading_weights[0], heading_weights[1]), \
        "Boundary weights should not depend on heading in this simplified model"

    print("smoke_poses_and_boundary: PASS")
    print(f"weights min/max: {min_weight:.6f}/{max_weight:.6f}")


if __name__ == "__main__":
    run_smoke_check()
