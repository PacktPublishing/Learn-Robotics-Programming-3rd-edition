import argparse
import json
from pathlib import Path

import numpy as np

LEFT = 0.0
RIGHT = 1500.0
BOTTOM = 0.0
TOP = 1500.0
CUTOUT_LEFT = 1000.0
CUTOUT_TOP = 500.0


def in_boundary(x, y):
    inside_walls = (x > LEFT) & (x < RIGHT) & (y > BOTTOM) & (y < TOP)
    not_in_cutout = ~((x > CUTOUT_LEFT) & (y < CUTOUT_TOP))
    return inside_walls & not_in_cutout


def near_boundary(x, y, margin_mm):
    near_outer = (
        (x - LEFT < margin_mm)
        | (RIGHT - x < margin_mm)
        | (y - BOTTOM < margin_mm)
        | (TOP - y < margin_mm)
    )
    near_cutout_vertical = (np.abs(x - CUTOUT_LEFT) < margin_mm) & (y < CUTOUT_TOP + margin_mm)
    near_cutout_horizontal = (np.abs(y - CUTOUT_TOP) < margin_mm) & (x > CUTOUT_LEFT - margin_mm)
    return near_outer | near_cutout_vertical | near_cutout_horizontal


def circular_mean(theta):
    return float(np.arctan2(np.mean(np.sin(theta)), np.mean(np.cos(theta))))


def summarize_entry(entry, margin_mm):
    poses = np.asarray(entry["poses"], dtype=np.float64)
    x = poses[:, 0]
    y = poses[:, 1]
    theta = poses[:, 2]

    inside = in_boundary(x, y)
    near = near_boundary(x, y, margin_mm)

    return {
        "step": int(entry["step"]),
        "time": float(entry["time"]),
        "ess": float(entry["ess"]),
        "inside_ratio": float(np.mean(inside)),
        "near_boundary_ratio": float(np.mean(near)),
        "mean_x": float(np.mean(x)),
        "mean_y": float(np.mean(y)),
        "std_x": float(np.std(x)),
        "std_y": float(np.std(y)),
        "mean_theta": circular_mean(theta),
    }


def read_trace(trace_path):
    entries = []
    with trace_path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number}: {exc}") from exc
    return entries


def main():
    parser = argparse.ArgumentParser(description="Analyse localisation JSONL trace output")
    parser.add_argument("trace_jsonl", type=Path, help="Path to localisation trace JSONL file")
    parser.add_argument("--margin-mm", type=float, default=75.0, help="Boundary margin for clustering metric")
    parser.add_argument(
        "--summary-json",
        type=Path,
        default=None,
        help="Optional path to write per-step summary as JSON",
    )
    args = parser.parse_args()

    entries = read_trace(args.trace_jsonl)
    if not entries:
        raise ValueError("Trace file contains no entries")

    summary = [summarize_entry(entry, args.margin_mm) for entry in entries]

    ess_values = np.array([s["ess"] for s in summary], dtype=np.float64)
    inside_values = np.array([s["inside_ratio"] for s in summary], dtype=np.float64)
    boundary_values = np.array([s["near_boundary_ratio"] for s in summary], dtype=np.float64)

    worst_boundary_idx = int(np.argmax(boundary_values))
    worst_inside_idx = int(np.argmin(inside_values))

    print(f"entries: {len(summary)}")
    print(f"ess min/median/max: {ess_values.min():.1f} / {np.median(ess_values):.1f} / {ess_values.max():.1f}")
    print(
        "inside_ratio min/median/max: "
        f"{inside_values.min():.3f} / {np.median(inside_values):.3f} / {inside_values.max():.3f}"
    )
    print(
        "near_boundary_ratio min/median/max: "
        f"{boundary_values.min():.3f} / {np.median(boundary_values):.3f} / {boundary_values.max():.3f}"
    )

    worst_boundary = summary[worst_boundary_idx]
    print(
        "max boundary clustering at step "
        f"{worst_boundary['step']}: near_boundary_ratio={worst_boundary['near_boundary_ratio']:.3f}, "
        f"inside_ratio={worst_boundary['inside_ratio']:.3f}, ess={worst_boundary['ess']:.1f}"
    )

    worst_inside = summary[worst_inside_idx]
    print(
        "lowest inside_ratio at step "
        f"{worst_inside['step']}: inside_ratio={worst_inside['inside_ratio']:.3f}, "
        f"near_boundary_ratio={worst_inside['near_boundary_ratio']:.3f}, ess={worst_inside['ess']:.1f}"
    )

    if args.summary_json:
        args.summary_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"wrote summary: {args.summary_json}")


if __name__ == "__main__":
    main()
