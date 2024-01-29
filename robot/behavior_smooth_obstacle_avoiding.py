from time import sleep
import mqtt_behavior
import numpy as np
import ujson as json

class ObstacleAvoidingBehavior:
    def __init__(self):
        self.sensor_data = None
        self.speed = 0.8

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")
        client.subscribe("sensors/distance_mm")
        client.message_callback_add("sensors/distance_mm", self.data_received)
        client.publish("sensors/distance/control/start_ranging", " ")

    def data_received(self, client, userdata, msg):
        try:
            self.sensor_data = json.loads(msg.payload)
        except Exception as err:
            print("Error:", err)
            print("Payload:", msg.payload)

    def get_speeds(self, nearest_distance):
        if nearest_distance >= 600:
            nearest_speed = self.speed
            furthest_speed = self.speed
            delay = 25
        elif nearest_distance > 400:
            nearest_speed = self.speed * 0.6
            furthest_speed = self.speed
            delay = 25
        elif nearest_distance > 300:
            nearest_speed = self.speed * 0.4
            furthest_speed = self.speed
            delay = 25
        elif nearest_distance > 150:
            nearest_speed = -self.speed * 0.4
            furthest_speed = self.speed
            delay = 25
        else: # collison
            nearest_speed = -self.speed * 0.6
            furthest_speed = self.speed * 0.6
            delay = 30
        return nearest_speed, furthest_speed, delay


    def run(self):
        client = mqtt_behavior.connect(self.on_connect)
        try:
            while True:
                # Do not call client loop - we already have a client loop in mqtt_behavior.connect
                sleep(0.1)
                if self.sensor_data is None:
                    continue
                as_array = np.array(self.sensor_data)
                self.sensor_data = None
                # Buckets for the sensor data - a 2 columns on the left, and two columns on the right.
                top_8_lines = as_array[:4, :]
                left_buckets = top_8_lines[:, :2]
                right_buckets = top_8_lines[:, -2:]
                # The distance is the minimum distance in each bucket.
                left_distance = int(np.min(left_buckets))
                right_distance = int(np.min(right_buckets))
                nearest_speed, furthest_speed, delay = self.get_speeds(min(left_distance, right_distance))
                if left_distance < right_distance:
                    left_motor_speed = nearest_speed
                    right_motor_speed = furthest_speed
                else:
                    left_motor_speed = furthest_speed
                    right_motor_speed = nearest_speed
                print(left_distance,right_distance,left_motor_speed,right_motor_speed)
                client.publish("log/obstacle_avoiding/smooth", json.dumps([left_distance,right_distance,nearest_speed,furthest_speed,left_motor_speed,right_motor_speed]))
                client.publish("motors/set_both", json.dumps([left_motor_speed, right_motor_speed]))
                sleep(delay * 0.0001)
        except KeyboardInterrupt:
            print("Stop requested")
        finally:
            print("Sending stop messages")
            client.publish("sensors/distance/control/stop_ranging", " ").wait_for_publish()
            client.publish("motors/stop", " ").wait_for_publish()
            client.disconnect()

behavior = ObstacleAvoidingBehavior()
behavior.run()
