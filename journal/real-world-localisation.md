# Real-World Localisation: Boundary-Only Investigation and Fix Plan

## Scope and objective

This plan targets a **boundary-only** Monte Carlo Localisation (MCL) workflow.

- Distance observation is intentionally disabled for this phase.
- Goal is not fastest convergence.
- Goal is: **usable, stable, in-bounds localisation** in real-world runs.

Usable means:

1. Particle cloud remains physically plausible (does not collapse into invalid/outside states).
2. Pose estimate converges to a consistent region across repeated runs.
3. Performance is slower than boundary+distance mode, but not unusable.

## Why the fixed arena is suitable for real-world experiments

The arena model is fixed: **1.5 m x 1.5 m** with a **0.5 m cutout**.

This cutout breaks radial symmetry and acts as a structural landmark for boundary-only localisation. In a pure square, mirrored hypotheses can remain ambiguous longer; the cutout should force one hypothesis to dominate as motion accumulates.

Conclusion: yes, this arena is valid and preferred for boundary-only real-world evaluation.

## Current status (already checked)

- Wall skew/shear alone is not sufficient to explain failure.
- FoV mismatch, invalid-reading handling, and basic zone orientation were checked and are unlikely primary cause.
- Wheelbase sensitivity appears high.
- Gear lash alone does not reproduce catastrophic MCL failure.

## Working hypothesis (ranked)

1. **Odometry bias + slip/compliance** dominates when boundary information is sparse.
2. **Timing dead-time** between encoder updates and other sensor streams causes stale updates and wrong resampling decisions.
3. **Overconfident motion model** collapses particle diversity before geometric cues from the cutout are fully used.

## Real-world experimental protocol (concise)

### A. Arena setup

- Build/mark the arena to match model dimensions.
- Use the start-pose dataset in `local_tools/simulation/experiment_start_poses.json`.
- The recorded measurements are stored in top-left coordinates, with converted bottom-left coordinates included for model use.
- Validate dataset consistency and L-shape bounds before running experiments:

```bash
uv run --project local_tools python local_tools/simulation/validate_start_poses.py
```

- Keep at least 6 repeatable start poses on the floor:
	- 2 near the cutout notch,
	- 2 near opposite full-wall corners,
	- 2 central/intermediate points.
- Mark heading arrows at each start point.

### B. Test trajectories

Run each trajectory from each start pose, 5 repeats minimum.

1. **Straight + stop**: 1.0 m forward in two segments.
2. **Square loop**: four equal legs with 90 degree turns.
3. **Rotate in place**: +180, -180.
4. **Cutout approach-turn**: approach cutout opening, turn, retreat.
5. **Kidnapped reset**: move robot manually mid-run, continue.

### Later section: trajectory implementation plans

Manual driving is likely too imprecise for consistent comparisons across runs.

Planned automation approach:

- Use closed-loop wheel speed control (encoder-driven) to improve repeatability of line and turn segments.
- Implement trajectory runner services derived from `BehaviorPath` rather than duplicating path-driving logic.
- Reuse `BehaviorPath` primitives such as `drive_line` and `drive_curve`.
- Create small scenario services for the first four trajectories (straight+stop, square loop, rotate in place, cutout approach-turn).
- Run each scenario service after placing the robot at a known start pose from `experiment_start_poses.json`.

Implementation notes:

- Keep each scenario service focused on sequence definition (segment lengths, turn angles, speeds), not motor-control internals.
- Use consistent names/tags so logger output maps directly to trajectory definitions.
- Keep kidnapped-reset as a partially manual intervention test, even when other trajectories are automated.

Proposed service names:

- `trajectory_straight_stop_service`
- `trajectory_square_loop_service`
- `trajectory_rotate_in_place_service`
- `trajectory_cutout_approach_turn_service`

Proposed common motion settings (initial values):

- `line_speed_mm_s = 140`
- `curve_speed_mm_s = 110`
- `pause_s = 0.75` between segments

Proposed segment definitions (v1):

1. `trajectory_straight_stop_service` (tag: `straight_stop`)
	- `drive_line(500 mm, 140 mm/s)`
	- pause 0.75 s
	- `drive_line(500 mm, 140 mm/s)`
	- pause 0.75 s

2. `trajectory_square_loop_service` (tag: `square_loop`)
	- Repeat 4x:
	  - `drive_line(350 mm, 140 mm/s)`
	  - pause 0.75 s
	  - `drive_curve(+90 deg, 110 mm/s)`
	  - pause 0.75 s

3. `trajectory_rotate_in_place_service` (tag: `rotate_in_place`)
	- `drive_curve(+180 deg, 110 mm/s)`
	- pause 0.75 s
	- `drive_curve(-180 deg, 110 mm/s)`
	- pause 0.75 s

4. `trajectory_cutout_approach_turn_service` (tag: `cutout_approach_turn`)
	- `drive_line(450 mm, 140 mm/s)`
	- pause 0.75 s
	- `drive_curve(+90 deg, 110 mm/s)`
	- pause 0.75 s
	- `drive_line(250 mm, 140 mm/s)`
	- pause 0.75 s
	- `drive_curve(+90 deg, 110 mm/s)`
	- pause 0.75 s
	- `drive_line(350 mm, 140 mm/s)`
	- pause 0.75 s

Run pattern:

- Place robot on a start pose from `experiment_start_poses.json`.
- Launch exactly one trajectory service.
- Start logger with matching `--tag`.
- Stop service and logger, then summarize with `mqtt_run_summary.py`.

### C. Metrics to record

For each run:

- In-bounds particle fraction over time.
- Pose cluster spread (radius or variance).
- Convergence time to stable cluster.
- Final pose error (ground-truth tape measurement).
- Failure type (outside collapse, wrong lobe lock, no convergence).

### D. Pass criteria (boundary-only)

- No persistent outside-boundary collapse.
- >= 90% runs remain in-bounds after initial transient.
- Final median error and spread are stable across repeats.
- Cutout-side disambiguation succeeds reliably from ambiguous starts.

## Minimal instrumentation to add (implementation)

Keep this lightweight and reversible.

1. Add sequence number and timestamp to encoder messages.
2. Add sequence number and timestamp to localisation output.
3. Log per-MCL-cycle diagnostics:
	- motion delta,
	- in-bounds particle ratio,
	- effective sample size (ESS),
	- resample trigger.
4. Keep logs as CSV/JSON lines for quick plotting.

This instrumentation is needed to prove whether divergence starts from motion input quality, timing, or filter confidence.

### Logging command for each run

Use the run logger to capture instrumentation streams to JSONL:

```bash
uv run --project local_tools python local_tools/pose_analysis/mqtt_run_logger.py
```

Add a scenario tag for easier filtering later:

```bash
uv run --project local_tools python local_tools/pose_analysis/mqtt_run_logger.py --tag square_loop
```

Default topics:

- `sensors/encoders/data`
- `localisation/poses_meta`
- `localisation/diagnostics`

Optional extra topics example:

```bash
uv run --project local_tools python local_tools/pose_analysis/mqtt_run_logger.py --topics "sensors/encoders/data,localisation/poses_meta,localisation/diagnostics,localisation/poses"
```

Summarize one run into one CSV row:

```bash
uv run --project local_tools python local_tools/pose_analysis/mqtt_run_summary.py local_tools/pose_analysis/logs/run-YYYYMMDD-HHMMSS.jsonl
```

Summarize the latest run automatically:

```bash
uv run --project local_tools python local_tools/pose_analysis/mqtt_run_summary.py --latest
```

Override or set tag at summary time:

```bash
uv run --project local_tools python local_tools/pose_analysis/mqtt_run_summary.py --latest --tag kidnapped_reset
```

This appends to `local_tools/pose_analysis/logs/run-summary.csv` by default.

## Simulator parity experiments

To validate causality, reproduce real failure shape in simulation by injecting:

- wheelbase bias,
- asymmetric slip,
- contact variation,
- timing delay/jitter.

Stop when simulation failure metrics match real-world patterns (not necessarily exact trajectories). That gives confidence in root cause.

## Candidate fix set (boundary-only compatible)

Apply smallest fixes first:

1. **Odometry calibration correction**
	- refine wheelbase and left/right distance scaling.
2. **Noise tuning for robustness**
	- increase motion noise where real odometry is demonstrably uncertain.
3. **Anti-collapse guardrail**
	- if invalid/outside fraction spikes, inject a controlled in-bounds recovery subset.
4. **Timing hygiene**
	- consume updates with explicit timestamps and reject excessively stale data.

## 2-4 page write-up template

Use this structure directly.

### Page 1: Problem and constraints

- Boundary-only objective and success definition.
- Why cutout arena is a valid landmarked geometry.
- Baseline symptoms.

### Page 2: Method

- Experimental protocol (starts, trajectories, repeats).
- Metrics and pass criteria.
- Instrumentation summary.

### Page 3: Results and diagnosis

- Before/after tables.
- Ranked root cause based on evidence.
- Failure-mode examples.

### Optional Page 4: Fix and rollout

- Minimal fix set.
- Regression checklist.
- Clear go/no-go acceptance criteria.

## Regression checklist

After any change, rerun at least:

- straight + stop,
- square loop,
- cutout approach-turn,
- kidnapped reset.

A change is accepted only if it improves stability across repeated runs, not just best-case outcomes.