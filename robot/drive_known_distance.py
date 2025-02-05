import json
from common.mqtt_behavior import connect, publish_json


class DriveKnownDistanceBehavior:
    expected_distance = 1000
    distance_reached = False
    speed = 0.8

    def check_distance_reached(self, client, userdata, msg):
        distance_data = json.loads(msg.payload)
        largest = max(distance_data['left_distance'], distance_data['right_distance'])
        if largest < self.expected_distance:
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
