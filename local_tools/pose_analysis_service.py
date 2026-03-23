#!/usr/bin/env python3
"""MQTT pose analysis service for localisation particle output.

Subscribes to `localisation/poses`, computes a representative pose vector,
and publishes it to `pose-analysis/data` as JSON:
    {"x": float, "y": float, "theta": float}

By default it computes the mean over all poses. An optional largest-cluster
mode can be enabled with `POSE_ANALYSIS_USE_LARGEST_CLUSTER=1`.
"""

import json
import importlib.util
import math
import os
import time
from pathlib import Path
from typing import Iterable


def load_mqtt_behavior_module():
    module_path = Path(__file__).resolve().parents[1] / "robot" / "common" / "mqtt_behavior.py"
    spec = importlib.util.spec_from_file_location("mqtt_behavior", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load mqtt_behavior from {module_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mqtt_behavior = load_mqtt_behavior_module()


INPUT_TOPIC = "localisation/poses"
OUTPUT_TOPIC = "pose-analysis/data"
DEFAULT_CLUSTER_BIN_MM = 80.0


def normalize_angle(theta: float) -> float:
    return theta % (2 * math.pi)


def circular_mean(angles: Iterable[float]) -> float:
    sin_sum = 0.0
    cos_sum = 0.0
    count = 0
    for theta in angles:
        sin_sum += math.sin(theta)
        cos_sum += math.cos(theta)
        count += 1

    if count == 0:
        return 0.0
    return normalize_angle(math.atan2(sin_sum / count, cos_sum / count))


def parse_pose_list(payload: bytes) -> list[tuple[float, float, float]]:
    parsed = json.loads(payload)
    if not isinstance(parsed, list):
        return []

    poses: list[tuple[float, float, float]] = []
    for item in parsed:
        try:
            if isinstance(item, dict):
                x = float(item["x"])
                y = float(item["y"])
                theta = float(item["theta"])
            elif isinstance(item, (list, tuple)) and len(item) >= 3:
                x = float(item[0])
                y = float(item[1])
                theta = float(item[2])
            else:
                continue
        except (KeyError, TypeError, ValueError):
            continue

        poses.append((x, y, normalize_angle(theta)))

    return poses


def largest_cluster(poses: list[tuple[float, float, float]], bin_size_mm: float) -> list[tuple[float, float, float]]:
    if not poses:
        return poses

    bins: dict[tuple[int, int], list[tuple[float, float, float]]] = {}
    for pose in poses:
        x, y, _ = pose
        key = (int(x // bin_size_mm), int(y // bin_size_mm))
        bins.setdefault(key, []).append(pose)

    return max(bins.values(), key=len)


def mean_pose(poses: list[tuple[float, float, float]]) -> dict[str, float]:
    x_mean = sum(p[0] for p in poses) / len(poses)
    y_mean = sum(p[1] for p in poses) / len(poses)
    theta_mean = circular_mean(p[2] for p in poses)
    return {
        "x": x_mean,
        "y": y_mean,
        "theta": theta_mean,
    }


def resolve_config_path() -> Path:
    explicit = os.getenv("POSE_ANALYSIS_CONFIG")
    if explicit:
        return Path(explicit).expanduser().resolve()

    repo_root = Path(__file__).resolve().parents[1]
    candidates = [
        repo_root / "local_tools" / "simulation" / ".env.json",
        repo_root / "robot_control" / ".env.json",
    ]
    for path in candidates:
        if path.exists():
            return path

    raise FileNotFoundError(
        "No config file found. Set POSE_ANALYSIS_CONFIG or create "
        "local_tools/simulation/.env.json"
    )


class PoseAnalysisService:
    def __init__(self):
        self.config_path = resolve_config_path()

        self.use_largest_cluster = os.getenv("POSE_ANALYSIS_USE_LARGEST_CLUSTER", "0") == "1"
        self.cluster_bin_mm = float(os.getenv("POSE_ANALYSIS_CLUSTER_BIN_MM", str(DEFAULT_CLUSTER_BIN_MM)))

    def on_connect(self, client, userdata, flags, rc: int):
        print(f"Connected to MQTT with result code {rc}")
        client.subscribe(INPUT_TOPIC)
        client.message_callback_add(INPUT_TOPIC, self.on_message)
        print(f"Subscribed to {INPUT_TOPIC}")

    def on_message(self, client, userdata, msg):
        try:
            poses = parse_pose_list(msg.payload)
            if not poses:
                return

            if self.use_largest_cluster:
                poses = largest_cluster(poses, self.cluster_bin_mm)

            output = mean_pose(poses)
            mqtt_behavior.publish_json(client, OUTPUT_TOPIC, output)
        except Exception as exc:
            print(f"Failed to process message on {msg.topic}: {exc}")

    def start(self):
        print(f"Using config from: {self.config_path}")
        print(
            "Strategy: "
            + (f"largest-cluster (bin={self.cluster_bin_mm}mm)" if self.use_largest_cluster else "mean-all")
        )

        mqtt_behavior.connect(on_connect=self.on_connect, config_path=str(self.config_path))

        while True:
            time.sleep(0.1)

if __name__ == "__main__":
    service = PoseAnalysisService()
    service.start()
