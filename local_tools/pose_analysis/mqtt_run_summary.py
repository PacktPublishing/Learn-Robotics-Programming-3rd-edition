#!/usr/bin/env python3
"""Summarize one MQTT run JSONL file into a compact CSV row.

Designed to work with logs produced by mqtt_run_logger.py.
"""

import argparse
import csv
import json
from pathlib import Path


ENCODER_TOPIC = "sensors/encoders/data"
POSES_META_TOPIC = "localisation/poses_meta"
DIAGNOSTICS_TOPIC = "localisation/diagnostics"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize one run JSONL log")
    parser.add_argument("input", nargs="?", default=None, help="Input JSONL log path")
    parser.add_argument(
        "--latest",
        action="store_true",
        help="Use the most recent run-*.jsonl file from local_tools/pose_analysis/logs",
    )
    parser.add_argument(
        "--csv",
        default=None,
        help="CSV output path (default: <input_dir>/run-summary.csv)",
    )
    parser.add_argument(
        "--tag",
        default=None,
        help="Optional scenario tag override for this summary row",
    )
    return parser.parse_args()


def default_logs_dir() -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    return repo_root / "local_tools" / "pose_analysis" / "logs"


def resolve_input_path(raw_input: str | None, use_latest: bool) -> Path:
    if raw_input:
        return Path(raw_input).expanduser().resolve()

    if use_latest:
        logs_dir = default_logs_dir()
        candidates = sorted(logs_dir.glob("run-*.jsonl"), key=lambda p: p.stat().st_mtime)
        if not candidates:
            raise FileNotFoundError(f"No run logs found in {logs_dir}")
        return candidates[-1].resolve()

    raise ValueError("Provide an input path or use --latest")


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    index = int(round((p / 100.0) * (len(ordered) - 1)))
    index = max(0, min(index, len(ordered) - 1))
    return float(ordered[index])


def mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return float(sum(values) / len(values))


def deltas(values: list[float]) -> list[float]:
    if len(values) < 2:
        return []
    return [values[i] - values[i - 1] for i in range(1, len(values))]


def load_records(input_path: Path) -> list[dict]:
    records: list[dict] = []
    with input_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict):
                records.append(record)
    return records


def summarize(records: list[dict], run_file: Path, tag_override: str | None = None) -> dict[str, float | int | str]:
    encoder_timestamps: list[float] = []
    meta_latency_ms: list[float] = []
    diagnostics_ess: list[float] = []
    diagnostics_in_bounds: list[float] = []
    received_timestamps: list[float] = []

    encoder_count = 0
    poses_meta_count = 0
    diagnostics_count = 0
    observed_tags: list[str] = []

    for record in records:
        received_ts = record.get("received_timestamp_ms")
        if isinstance(received_ts, (int, float)):
            received_timestamps.append(float(received_ts))

        topic = record.get("topic")
        payload = record.get("payload")
        record_tag = record.get("tag")
        if isinstance(record_tag, str) and record_tag:
            observed_tags.append(record_tag)
        if not isinstance(payload, dict):
            continue

        if topic == ENCODER_TOPIC:
            encoder_count += 1
            source_ts = payload.get("timestamp_ms")
            if isinstance(source_ts, (int, float)):
                encoder_timestamps.append(float(source_ts))

        elif topic == POSES_META_TOPIC:
            poses_meta_count += 1
            source_ts = payload.get("source_encoder_timestamp_ms")
            loc_ts = payload.get("timestamp_ms")
            if isinstance(source_ts, (int, float)) and isinstance(loc_ts, (int, float)):
                meta_latency_ms.append(float(loc_ts) - float(source_ts))

        elif topic == DIAGNOSTICS_TOPIC:
            diagnostics_count += 1
            ess = payload.get("effective_sample_size")
            in_bounds = payload.get("in_bounds_ratio")
            if isinstance(ess, (int, float)):
                diagnostics_ess.append(float(ess))
            if isinstance(in_bounds, (int, float)):
                diagnostics_in_bounds.append(float(in_bounds))

    encoder_periods = deltas(sorted(encoder_timestamps))

    start_ms = min(received_timestamps) if received_timestamps else 0.0
    end_ms = max(received_timestamps) if received_timestamps else 0.0
    duration_s = (end_ms - start_ms) / 1000.0 if end_ms >= start_ms else 0.0
    inferred_tag = tag_override
    if inferred_tag is None and observed_tags:
        inferred_tag = observed_tags[0]

    return {
        "run_file": str(run_file),
        "tag": inferred_tag or "",
        "records_total": len(records),
        "duration_s": round(duration_s, 3),
        "encoder_count": encoder_count,
        "poses_meta_count": poses_meta_count,
        "diagnostics_count": diagnostics_count,
        "encoder_period_ms_mean": round(mean(encoder_periods), 3),
        "encoder_period_ms_p95": round(percentile(encoder_periods, 95), 3),
        "meta_latency_ms_mean": round(mean(meta_latency_ms), 3),
        "meta_latency_ms_p95": round(percentile(meta_latency_ms, 95), 3),
        "diag_ess_mean": round(mean(diagnostics_ess), 3),
        "diag_ess_min": round(min(diagnostics_ess), 3) if diagnostics_ess else 0.0,
        "diag_in_bounds_mean": round(mean(diagnostics_in_bounds), 6),
        "diag_in_bounds_min": round(min(diagnostics_in_bounds), 6) if diagnostics_in_bounds else 0.0,
    }


def append_csv(output_csv: Path, summary: dict[str, float | int | str]) -> None:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    write_header = not output_csv.exists()
    with output_csv.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary.keys()))
        if write_header:
            writer.writeheader()
        writer.writerow(summary)


def main() -> None:
    args = parse_args()
    input_path = resolve_input_path(args.input, args.latest)
    output_csv = (
        Path(args.csv).expanduser().resolve()
        if args.csv
        else input_path.parent / "run-summary.csv"
    )

    records = load_records(input_path)
    summary = summarize(records, input_path, tag_override=args.tag)
    append_csv(output_csv, summary)

    print(json.dumps(summary, indent=2))
    print(f"Appended summary row to: {output_csv}")


if __name__ == "__main__":
    main()
