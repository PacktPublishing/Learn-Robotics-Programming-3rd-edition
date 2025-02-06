import ujson as json

from common.mqtt_behavior import connect, publish_json
from common.pid_controller import PIDController


class DriveStraightLineBehavior:
    def __init__(self):
        self.speed = 0.6
        self.balance_pid = PIDController(0.01)

    def on_encoders_data(self, client, userdata, message):
        encoder_data = json.loads(message.payload)
        left_encoder = encoder_data['left_distance']
        right_encoder = encoder_data['right_distance']
        # Get the error
        error = left_encoder - right_encoder
        # Balance the motors
        balance = self.balance_pid.control(error)
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
