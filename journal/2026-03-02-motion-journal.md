# 2026-03-02 Motion journal

Ideas for motion assymetry problem:

- Our encoders are returning a distance, and making the localisation do the subtraction. We can get radians delta during encoder capture, then apply the radians to mm calculations, and transmit this on mqtt.
- We can "tag" poses, ince they are resampled, not regenerated, and track how poses evolve over time somehow... If we can see this, we can see the skew.
- We could swap our guassians on motion noise for triagular distributions, so the noise is more bounded, we don't expect a very distance point to be prossible.

## Pose tagging

I'd like to tag poses with a "parent pose" when the new generation is made. 
We can reduce the pose count right down to 20 for this exercise, and tighten the noise right down.

What I want to do is track the assymetry - if we draw the path of the poses as they are moved and resampled, a skew should become visible.

This would be a web page, showing the poses, with lines from a parent pose to the children, such that hovering a line will show the route back to the great grandparent. We should also see which linages are more successful than others, and which ones are being resampled out.

