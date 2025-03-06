import ujson as json
import time

from common.mqtt_behavior import connect, publish_json
from common.pid_controller import PIDController


class DriveStraightLineBehavior:
    def __init__(self):
        self.speed = 0.6
        self.balance_pid = PIDController(0.0001)
        self.last_update = time.time()

    def on_encoders_data(self, client, userdata, message):
        encoder_data = json.loads(message.payload)
        left_encoder = encoder_data['left_mm_per_sec']
        right_encoder = encoder_data['right_mm_per_sec']
        new_time = time.time()
        time_difference = new_time - self.last_update
        self.last_update = new_time

        # Get the error
        error = left_encoder - right_encoder

        # Balance the motors
        balance = self.balance_pid.control(error, time_difference)
        publish_json(client, "drive_straight_line/plot", {
            "error": error,
            "integral": self.balance_pid.integral,
            "time": new_time})

        left_speed = self.speed - balance
        right_speed = self.speed + balance
        publish_json(client, "motors/wheels", [left_speed, right_speed])

    def start(self):
        client = connect(start_loop=False)
        client.subscribe("sensors/encoders/data")
        client.publish("sensors/encoders/control/reset")
        client.message_callback_add("sensors/encoders/data",
                                    self.on_encoders_data)
        client.loop_forever()


behavior = DriveStraightLineBehavior()
behavior.start()
