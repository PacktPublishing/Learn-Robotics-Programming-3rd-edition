class PIDController:
    def __init__(self, proportional_constant):
        self.proportional_constant = proportional_constant

    def control(self, error):
        return self.proportional_constant * error
