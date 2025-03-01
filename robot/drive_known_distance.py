import ujson as json
import time
from common.mqtt_behavior import connect, publish_json


class DriveKnownDistanceBehavior:
    expected_distance = 1000
    distance_reached = False
    speed = 0.8

    def check_distance_reached(self, client, userdata, msg):
        distance_data = json.loads(msg.payload)
        left_error = self.expected_distance - distance_data['left_distance']
        right_error = self.expected_distance - distance_data['right_distance']
        publish_json(client, "drive_known_distance/plot", {
            "left_error": left_error,
            "right_error": right_error,
            "time": time.time()
        })
        largest = max(right_error, left_error)
        if largest > 0:
            publish_json(client, "motors/wheels", [self.speed, self.speed])
        else:
            client.publish("motors/stop")
            self.distance_reached = True

    def start(self):
        client = connect(start_loop=False)
        client.subscribe("sensors/encoders/data")
        client.publish("sensors/encoders/control/reset")
        client.message_callback_add("sensors/encoders/data",
                                    self.check_distance_reached)
        while not self.distance_reached:
            client.loop()


behavior = DriveKnownDistanceBehavior()
behavior.start()
