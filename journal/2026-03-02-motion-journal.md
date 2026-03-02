# 2026-03-02 Motion journal

Ideas for motion assymetry problem:

- Our encoders are returning a distance, and making the localisation do the subtraction. We can get radians delta during encoder capture, then apply the radians to mm calculations, and transmit this on mqtt.
- We can "tag" poses, ince they are resampled, not regenerated, and track how poses evolve over time somehow... If we can see this, we can see the skew.
