class PController:
    def __init__(self, k_p):
        self.k_p = k_p

    def control(self, error):
        return self.k_p * error


class PIController(PController):
    def __init__(self, k_p, k_i):
        super().__init__(k_p)
        self.k_i = k_i
        self.integral = 0

    def control(self, error, dt=1):
        self.integral += error * dt
        return self.k_p * error + self.k_i * self.integral
