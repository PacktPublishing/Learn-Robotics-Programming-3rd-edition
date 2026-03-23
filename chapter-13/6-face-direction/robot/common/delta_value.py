
class DeltaValue:
    def __init__(self):
        self.previous = None
        self.current = 0

    def set_current(self, value):
        self.current = value

    def consume_delta(self):
        if self.previous is None:
            delta = 0
        else:
            delta = self.current - self.previous
        self.previous = self.current
        return delta
