# Motor timing profiling

Date: 2026-02-28
Branch: `chapter-17/motor-timing`

## What was instrumented

Profiling was added around `set_motor_wheels` in `robot/inventor_hat_service.py`:

- timestamp before `left_motor.speed(left)`
- timestamp after left call / before right call
- timestamp after `right_motor.speed(right)`

From those timings we publish:

- `avg_gap_us`: average time from start to completion of left call (proxy for left-right command skew)
- `max_gap_us`: max observed left-right skew proxy
- `avg_total_us`: average time for both motor calls
- `max_total_us`: max observed total time for both calls

Timing summaries are published to MQTT topic `motors/wheels/timing` and visualised via `robot_control/motor_timing_widget.js`.

## Observed results

- Samples: 1200
- Avg gap (μs): 1439.84
- Max gap (μs): 52545.39
- Avg total (μs): 2676.52
- Max total (μs): 53771.13

## Interpretation

- Typical skew between wheel command calls is ~1.44 ms, which is generally small and likely acceptable for closed-loop wheel control.
- Typical total command update cost is ~2.68 ms, also reasonable for Python + I2C command path.
- Rare spikes (~53 ms) exist; these are likely scheduler/I2C contention outliers and may cause occasional transient twitch but should not dominate average behaviour.

## Practical takeaway

This timing profile suggests command-call skew is unlikely to be the primary cause of persistent wheel bias.
A more likely source would be calibration / drivetrain asymmetry / control tuning, with occasional jitter from runtime spikes.

## Follow-up ideas

- Add p95/p99 timing metrics (not just max)
- Count threshold exceedances (e.g. gap > 5 ms, > 10 ms)
- Correlate timing spikes with encoder error events
