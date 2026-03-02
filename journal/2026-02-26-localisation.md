# 2026-02-26 Localisation

Yesterday I discovered that modelling asymmetry in the encoders gave the closest simulation match to the real world behavior of the robot, more so than varying the wheelbase, wheel size, or adding symmetric noise.

ONe suggestion from an LLM was that the noise that we'd put into the simulation and also the model tends to be guassian around a particular point, which it makes it not great in compensating for an assymetry

The real robot is assymetrically weighted. I asumed however that since the gearing and encoders should be symmetric that this would be iroed out by the encoders.

I had to add encoder symmetry to the simulation though. 
Where the encoders will not mirror the real world is wheel contact - if the weight means that wheels have assymetric contact points, or there's a slight assymetry in wheel sizes.

I attempted to compensate for this with encoder scaling values, and simply adjusting by hand until I got something close. 

## New ideas

We should see if there's a way to systematically eliminate this assymetry or compensate for it.I'm not going to get perfect wheels or weighting, so how?

Ideas:

1. Wait for real converging in localisation (wrong points). THen move the robot to match this pose - lift up and place close to the cluster orientation and position. NOw drive the robot again, and watch how the poses move with the real robot - how far off does it go, and in what direction. Is it distance or assymetric theta that is off? Start with 0 weighting on the encoders.
2. Use a straight line on the floor. PErform a straight line drive, and track the drift, then try compensating in encoder weightings.
3. Adding noise to encoders will be unlikely to help, since there's already a noise model in the motion model, and the problem is more of a bias than noise. However, we could try adding a bias term to the encoder readings in the model to see if that helps.
4. Consider if there's a way to physically adjust the robot to reduce the asymmetry, such as adding weight to the lighter side or adjusting the wheel alignment. This is unlikely to be perfect. However, moving the battery around is likely to reduce this asymmetry, and is worth trying. I've adjusted this now - let's try a rerun.

## Problem

- Drive known distance resets the encoders. Can we get a distance reading to start instead, and work from there instead of the reset. - fixed.

## Test results

1 - The encoder readings are pulling slightly to the right. Let's try biasing it back to the left with a weighting of 0.98 on the right encoder, and 1.00 on the left encoder. This is a bit of a hack, but it seems to be working well in the simulation, and is likely to be close to the real world behavior.
And now - it's pulled to the left instead. SO let's bring that to 0.99 and 1.00.