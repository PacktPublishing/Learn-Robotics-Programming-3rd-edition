class PIDController:
    def __init__(self, proportional_constant, integral_constant=0):
        self.proportional_constant = proportional_constant
        self.integral_constant = integral_constant
        self.integral = 0

    def control(self, error, time_difference=1):
        self.integral += error * time_difference
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
