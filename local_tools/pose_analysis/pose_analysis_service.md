# Pose Analysis Service

Consumes localisation particle output and publishes a representative pose.

- Input topic: `localisation/poses`
- Output topic: `pose-analysis/data`
- Output payload: `{ "x": <float>, "y": <float>, "theta": <float radians> }`

## Run

From repo root:

```bash
python local_tools/pose_analysis/pose_analysis_service.py
```

The service reads MQTT credentials from:
1. `POSE_ANALYSIS_CONFIG` (if set), otherwise
2. `local_tools/simulation/.env.json`, otherwise
3. `robot_control/.env.json`

## Optional largest-cluster mode

Default behavior publishes mean of all poses (`mean-all`).

To follow the densest pose region:

```bash
POSE_ANALYSIS_USE_LARGEST_CLUSTER=1 python local_tools/pose_analysis/pose_analysis_service.py
```

Tune cluster bin size (millimeters):

```bash
POSE_ANALYSIS_USE_LARGEST_CLUSTER=1 POSE_ANALYSIS_CLUSTER_BIN_MM=60 python local_tools/pose_analysis/pose_analysis_service.py
```
