class PIDController:
    def __init__(self, proportional_constant, integral_constant=0,
                 reset_on_sign_change=False):
        self.proportional_constant = proportional_constant
        self.integral_constant = integral_constant
        self.integral = 0
        self.last_error = 0
        self.reset_on_sign_change = reset_on_sign_change

    def control(self, error, time_difference=1):
        self.integral += error * time_difference
        if self.reset_on_sign_change and self.last_error * error < 0:
            self.integral = 0
        self.last_error = error
        return self.proportional_constant * error \
            + self.integral_constant * self.integral
