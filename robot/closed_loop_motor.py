import ujson as json
import time

from common.mqtt_behavior import connect, publish_json
from common.pid_controller import PIDController


class ClosedLoopMotorBehavior:
    def __init__(self):
        self.mm_per_second = 200
        self.left_pid = PIDController(0.004, 0.008)
        self.right_pid = PIDController(0.004, 0.008)
        self.last_update = time.time()

    def on_encoders_data(self, client, userdata, message):
        encoder_data = json.loads(message.payload)
        left_encoder = encoder_data['left_mm_per_sec']
        right_encoder = encoder_data['right_mm_per_sec']
        new_time = time.time()
        time_difference = new_time - self.last_update
        self.last_update = new_time

        # Get the error
        left_error = self.mm_per_second - left_encoder
        right_error =  self.mm_per_second - right_encoder
        left_control = self.left_pid.control(left_error, time_difference)
        right_control = self.right_pid.control(right_error, time_difference)
        publish_json(client, "closed_loop_motor/plot", {
            "left_error": left_error, "left_control": left_control,
            "right_error": right_error, "right_control": right_control,
            "time": new_time})

        left_speed = left_control
        right_speed = right_control
        publish_json(client, "motors/wheels", [left_speed, right_speed])

    def start(self):
        client = connect(start_loop=False)
        client.publish("sensors/encoders/control/reset")
        client.subscribe("sensors/encoders/data")
        client.message_callback_add("sensors/encoders/data",
                                    self.on_encoders_data)
        client.loop_forever()

behavior = ClosedLoopMotorBehavior()
behavior.start()
