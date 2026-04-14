# Localisation Trace Findings (2026-03-31)

## Summary

- The trace file contains two appended runs. The relevant run appears to be run 2 with 274 updates.
- In run 2, the particle cloud remains largely ambiguous for roughly the first 100 steps (high ESS and mean pose near arena center), so the boundary-only observation model is not strongly discriminative in free space.
- The filter later collapses into implausible hypotheses:
  - Worst frame: step 235 with inside_ratio 0.225 and near_boundary_ratio 0.825.
  - Final frame: step 274 with ESS 2627.0 and dominant clusters outside the arena.
- The cloud sometimes still contains particles near both estimated real start and real end at the same time, which indicates weak state discrimination from the current observation model.
- The strongest signal is odometry inconsistency:
  - Integrating logged odometry from estimated real start (1350, 600, 190 deg) ends near (1352.5, 1496.2, 191.2 deg), not near the reported real end (~200, 600, ~135 deg).
  - This points more to motion model / coordinate convention mismatch than ESS logic.
- Alternative translation conventions were tested against the same logged odometry. A form equivalent to x += -sin(theta) * d, y += cos(theta) * d produced an endpoint near (453.8, 602.5), which is directionally closer to observed motion than the current convention.

## How We Got There

1. Ran coarse trace summary on the downloaded JSONL file.

   - Command:
     - /home/danny/git_work/0-projects/Learn-Robotics-Programming-3rd-edition/.venv/bin/python /home/danny/git_work/0-projects/Learn-Robotics-Programming-3rd-edition/chapter-12/complete-plus-ess/experiments/analyse_localisation_trace.py /home/danny/git_work/0-projects/Learn-Robotics-Programming-3rd-edition/chapter-12/complete-plus-ess/localisation_trace.jsonl

   - Key output:
     - entries: 299
     - ess min/median/max: 1768.9 / 13023.6 / 19303.0
     - inside_ratio min/median/max: 0.225 / 0.888 / 0.990
     - near_boundary_ratio min/median/max: 0.052 / 0.256 / 0.825
     - max boundary clustering at step 235 with inside_ratio 0.225

2. Measured support for estimated real start/end poses and headings across frames.

   - Start estimate: (1350, 600, 190 deg)
   - End estimate: (200, 600, 135 deg)

   - Findings:
     - Early frames had nonzero support near both hypotheses.
     - Around steps 189 to 201 there were still many particles near both locations.
     - By late frames, heading-consistent support for the real end was effectively zero.

3. Checked continuity of step counters to detect appended runs.

   - Found one reset: step 25 to step 1.
   - Split result:
     - run 1: 25 entries
     - run 2: 274 entries

4. Examined dominant spatial bins in key frames.

   - Frames 189 to 201: dominant bins mostly upper-right region.
   - Step 235: many dominant bins out of bounds.
   - Step 274 (final): dominant bins include negative x and y > top, indicating cloud drift to impossible regions.

5. Summed odometry in run 2 to compare implied motion against observed robot behavior.

   - Total translation: 4445.3 mm
   - Total theta: -6.262 rad (-358.8 deg)
   - Integrated dead-reckoning from estimated real start ended near (1352.5, 1496.2, 191.2 deg)

   This is incompatible with the reported end around (200, 600, 135 deg).

6. Tested alternative translation conventions against the same logged odometry.

   - Current convention effectively behaved like x += cos(theta) * d, y += sin(theta) * d.
   - A tested alternative equivalent to x += -sin(theta) * d, y += cos(theta) * d produced (453.8, 602.5, 191.2 deg), much closer in translational trend.

7. Conclusion reached.

   - The data supports that the major failure is likely in motion model / coordinate convention alignment (and/or wheel encoder sign/ordering), with boundary-only observation weakness as a secondary factor.
