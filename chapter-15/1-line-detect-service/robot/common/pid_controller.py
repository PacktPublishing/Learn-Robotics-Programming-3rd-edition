import numpy as np


class PIDController:
    def __init__(self, proportional_constant, integral_constant=0, smart_reset=False,
                 windup_limit=None):
        self.proportional_constant = proportional_constant
        self.integral_constant = integral_constant
        self.integral = 0
        self.smart_reset = smart_reset
        self.windup_limit = windup_limit

    def control(self, error, time_difference=1):
        if self.smart_reset and np.sign(error) != np.sign(self.integral):
            self.reset()
        self.integral += error * time_difference
        if self.windup_limit is not None:
            # Prevent integral windup
            self.integral = np.clip(
                self.integral,
                -self.windup_limit, self.windup_limit)
        return self.proportional_constant * error \
            + self.integral_constant * self.integral

    def reset(self):
        self.integral = 0

    def handle_config_messages(self, data, prefix):
        if prefix + '/proportional' in data:
            self.proportional_constant = data[prefix + '/proportional']
        if prefix + '/integral' in data:
            self.integral_constant = data[prefix + '/integral']
            self.integral = 0
