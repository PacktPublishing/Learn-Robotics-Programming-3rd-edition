# Real-World Localisation Notes

This document captures likely causes of localisation drift when moving from the rectilinear simulation arena to a real-world arena, plus specific sensor-model mismatches identified in the codebase and VL53L5CX datasheet.

## Major causes to consider

- Map mismatch: real walls are not perfectly straight or orthogonal, which can push pose estimates out of bounds. - Eliminated - the model copes with even large distortion through shearing 
- Sensor model mismatch: incorrect field of view, invalid reading handling, or zone orientation can bias the observation likelihood.
- Odometry drift: wheel slip, uneven floor, and encoder calibration issues accumulate quickly.
- Map alignment errors: coordinate frame origin, rotation, or scale mismatches between real arena and model.
- Overconfident filter: noise parameters too small cause premature convergence on incorrect poses.

## VL53L5CX datasheet highlights

- Detection volume FoV: 45 degrees horizontal, 45 degrees vertical, 65 degrees diagonal.
- Ranging per zone: 2 cm to 400 cm.
- Zone mapping orientation: captured image is flipped horizontally and vertically by the RX lens. Zone 0 corresponds to the top-right of the scene (per datasheet effective orientation section).
- Max ranging depends on reflectance and ambient light; full 400 cm is best-case.

## Code/model mismatches checked and eliminated

- Field of view usage: sim and observation model both use 45 degrees; diagonal 65 degrees does not explain the issue.
- Minimum range clamping: 20 mm min is already covered by noise; accepting 0 mm is not causing drift.
- Invalid readings handling: 3000 mm substitution does not create a phantom wall given arena max ~1500 mm.
- Zone orientation and floor filtering: verified that sim and real sensor orientation align; floor row drop is not discarding obstacles.
- Sensor forward offset mismatch: boundary model makes the exact offset non-causal for the observed issue.

## Suggested checks/fixes

- Recalibrate odometry parameters and process noise if drift persists.
- Validate map alignment (origin, rotation, scale) between the real arena and model. - eliminated.
- Confirm the real arena geometry matches the model expectations beyond straightness (e.g., skew, scale, and offsets). - eliminated.

## Mechanical effects to model next

- Gear lash: wheels can rotate ~1 degree before the encoder chain engages, causing a deadband in odometry for small motions.
- Wheel camber and compliance: motor mounts allow slight swing, shifting contact patch toward the inner tire edge and changing effective rolling radius.
- Tire deformation: soft TT-motor tires compress under load, altering wheel radius and creating load-dependent slip.
- Wheelbase sensitivity: small wheelbase errors caused much larger localisation failure than global arena shear.

## Plan of action (next steps)

- Simulate gear lash with an angular deadband before encoder counts accumulate, then re-run localisation convergence tests.
- Simulate camber/compliance by biasing the effective wheel radius based on load or tilt assumptions.
- Simulate tire deformation as a small, load-dependent reduction in wheel radius and increased slip variance.
- Re-run the shear tests with the above mechanical distortions combined to quantify cumulative effects.
- Use results to set realistic process noise and encoder calibration targets for the real robot.

## Verified

- Measured and updated wheel base, including wheel flex.
- Measured and updated wheel diameter.
- Improved the arena edges and corners (not all are perfect yet).
- Improved the distance sensor service to reconnect if it starts too early.

## Gear lash experiments

Simulated gear lash, with encoders leading by 1, 2, 4,8  and 16 degrees has not caused a problem with the MCL, it does increase the chances of the robot hitting the wall though.