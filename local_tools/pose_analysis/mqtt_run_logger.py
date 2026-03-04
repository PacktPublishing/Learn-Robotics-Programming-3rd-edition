#!/usr/bin/env python3
"""MQTT run logger for localisation experiments.

Subscribes to selected topics and writes one JSON object per message to a
JSONL file, making it easy to analyze in notebooks or scripts.
"""

import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path

from robot.common import mqtt_behavior


DEFAULT_TOPICS = [
    "sensors/encoders/data",
    "localisation/poses_meta",
    "localisation/diagnostics",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Log MQTT topics to JSONL")
    parser.add_argument(
        "--output",
        default=None,
        help="Path to JSONL output file (default: local_tools/pose_analysis/logs/<timestamp>.jsonl)",
    )
    parser.add_argument(
        "--topics",
        default=None,
        help="Comma-separated list of MQTT topics to subscribe to",
    )
    parser.add_argument(
        "--tag",
        default=None,
        help="Optional scenario tag to include in each record (e.g. square_loop)",
    )
    return parser.parse_args()


def default_output_path() -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    logs_dir = repo_root / "local_tools" / "pose_analysis" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return logs_dir / f"run-{stamp}.jsonl"


def parse_topics(raw_topics: str | None) -> list[str]:
    env_topics = os.getenv("RUN_LOGGER_TOPICS")
    selected = raw_topics if raw_topics is not None else env_topics
    if not selected:
        return DEFAULT_TOPICS
    topics = [topic.strip() for topic in selected.split(",") if topic.strip()]
    return topics if topics else DEFAULT_TOPICS


class RunLogger:
    def __init__(self, output_path: Path, topics: list[str], tag: str | None):
        self.output_path = output_path
        self.topics = topics
        self.tag = tag
        self.file_handle = self.output_path.open("a", encoding="utf-8", buffering=1)

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected to MQTT with result code {rc}")
        for topic in self.topics:
            client.subscribe(topic)
            client.message_callback_add(topic, self.on_message)
            print(f"Subscribed: {topic}")

    def on_message(self, client, userdata, msg):
        received_timestamp_ms = int(time.time() * 1000)
        payload_text = msg.payload.decode("utf-8", errors="replace")
        try:
            payload = json.loads(payload_text)
        except json.JSONDecodeError:
            payload = payload_text

        record = {
            "received_timestamp_ms": received_timestamp_ms,
            "topic": msg.topic,
            "payload": payload,
        }
        if self.tag:
            record["tag"] = self.tag
        self.file_handle.write(json.dumps(record) + "\n")

    def start(self):
        print(f"Writing logs to: {self.output_path}")
        print(f"Topics: {', '.join(self.topics)}")

        mqtt_behavior.connect(on_connect=self.on_connect)

        while True:
            time.sleep(0.1)


def main():
    args = parse_args()
    output_path = Path(args.output).expanduser().resolve() if args.output else default_output_path()
    topics = parse_topics(args.topics)
    logger = RunLogger(output_path=output_path, topics=topics, tag=args.tag)
    logger.start()


if __name__ == "__main__":
    main()
