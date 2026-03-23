import time

class TimeStepper:
    def __init__(self):
        self.last_update = time.time()

    def step(self):
        new_time = time.time()
        time_difference = new_time - self.last_update
        self.last_update = new_time
        return time_difference

## For the integral, we are goign to make another building block, a time stepper.
## It simply tracks how much time we've stepped forward, which for now we can pass to the PID controller.
