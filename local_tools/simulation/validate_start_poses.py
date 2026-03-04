#!/usr/bin/env python3
"""Validate experiment start poses dataset for localisation experiments."""
import argparse
import json
import math
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate experiment_start_poses.json")
    parser.add_argument(
        "--input",
        default="local_tools/simulation/experiment_start_poses.json",
        help="Path to start poses JSON file",
    )
    parser.add_argument(
        "--theta-tolerance",
        type=float,
        default=1e-6,
        help="Allowed absolute difference for theta_pi consistency check",
    )
    return parser.parse_args()


def is_inside_l_shape(x_mm: float, y_mm: float, width_mm: float, height_mm: float, cutout_x_min_mm: float, cutout_y_max_mm: float) -> bool:
    in_square = 0 <= x_mm <= width_mm and 0 <= y_mm <= height_mm
    in_cutout = x_mm > cutout_x_min_mm and y_mm < cutout_y_max_mm
    return in_square and not in_cutout


def main():
    args = parse_args()
    input_path = Path(args.input).expanduser().resolve()

    with input_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    arena = data["arena"]
    width_mm = float(arena["width_mm"])
    height_mm = float(arena["height_mm"])
    cutout_x_min_mm = float(arena["cutout"]["x_min_mm"])
    cutout_y_max_mm = float(arena["cutout"]["y_max_mm"])

    failures: list[str] = []
    poses = data.get("start_poses", [])

    for pose in poses:
        pose_id = pose.get("id", "<unknown>")

        x_tl = float(pose["x_top_left_mm"])
        y_tl = float(pose["y_top_left_mm"])
        x_bl = float(pose["x_bottom_left_mm"])
        y_bl = float(pose["y_bottom_left_mm"])

        expected_y_bl = height_mm - y_tl
        if abs(y_bl - expected_y_bl) > 1e-6:
            failures.append(
                f"{pose_id}: y conversion mismatch (expected {expected_y_bl}, got {y_bl})"
            )

        if abs(x_bl - x_tl) > 1e-6:
            failures.append(
                f"{pose_id}: x conversion mismatch (expected {x_tl}, got {x_bl})"
            )

        theta_deg = float(pose["theta_deg"])
        theta_pi = float(pose["theta_pi"])
        expected_theta_pi = theta_deg / 180.0
        if abs(theta_pi - expected_theta_pi) > args.theta_tolerance:
            failures.append(
                f"{pose_id}: theta_pi mismatch (expected {expected_theta_pi}, got {theta_pi})"
            )

        if not is_inside_l_shape(x_bl, y_bl, width_mm, height_mm, cutout_x_min_mm, cutout_y_max_mm):
            failures.append(
                f"{pose_id}: outside L-shape arena at bottom-left coords ({x_bl}, {y_bl})"
            )

    print(f"Checked {len(poses)} start poses in {input_path}")
    if failures:
        print("Validation FAILED:")
        for failure in failures:
            print(f"- {failure}")
        exit(1)

    theta_pi_values = [float(p["theta_pi"]) for p in poses]
    theta_rad_values = [value * math.pi for value in theta_pi_values]
    print("Validation PASSED")
    print(f"Theta range (pi units): {min(theta_pi_values):.6f} .. {max(theta_pi_values):.6f}")
    print(f"Theta range (radians): {min(theta_rad_values):.6f} .. {max(theta_rad_values):.6f}")

if __name__ == "__main__":
    main()
