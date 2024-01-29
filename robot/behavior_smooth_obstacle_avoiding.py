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
        # Invite the reader to adjust these values to see how the robot behaves.
        if nearest_distance >= 400:
            furthest_speed = self.speed
            nearest_speed = self.speed
            delay = 25
        elif nearest_distance > 300:
            furthest_speed = self.speed * 0.6
            nearest_speed = self.speed
            delay = 25
        elif nearest_distance > 200:
            furthest_speed = self.speed * 0.4
            nearest_speed = self.speed
            delay = 25
        elif nearest_distance > 150:
            furthest_speed = -self.speed * 0.4
            nearest_speed = self.speed
            delay = 25
        else:
            furthest_speed = -self.speed * 0.6
            nearest_speed = self.speed
            delay = 30
        return nearest_speed, furthest_speed, delay

    def act(self):
        as_array = np.array(self.sensor_data)
        self.sensor_data = None
        # Buckets for the sensor data - a 2 columns on the left, and two columns on the right.
        top_lines = as_array[:4, :]
        left_sensors = top_lines[:, :2]
        right_sensors = top_lines[:, -2:]
        # The distance is the minimum distance in each bucket.
        # >>> type(np.min(data) )
        # <class 'numpy.int64'>
        left_distance = int(np.min(left_sensors))
        right_distance = int(np.min(right_sensors))
        nearest_speed, furthest_speed, delay = self.get_speeds(min(left_distance, right_distance))
        if left_distance < right_distance:
            left_motor_speed = nearest_speed
            right_motor_speed = furthest_speed
        else:
            left_motor_speed = furthest_speed
            right_motor_speed = nearest_speed
        print(left_distance,right_distance,left_motor_speed,right_motor_speed)
        self.client.publish("log/obstacle_avoiding/smooth", json.dumps([left_distance,right_distance,nearest_speed,furthest_speed,left_motor_speed,right_motor_speed]))
        self.client.publish("motors/set_both", json.dumps([left_motor_speed, right_motor_speed]))
        sleep(delay * 0.001)

    def run(self):
        self.client = mqtt_behavior.connect(self.on_connect)
        try:
            while True:
                # Do not call client loop - we already have a client loop in mqtt_behavior.connect
                if self.sensor_data is not None:
                    self.act()
                sleep(0.01)
        except KeyboardInterrupt:
            print("Stop requested")
        finally:
            print("Sending stop messages")
            self.client.publish("sensors/distance/control/stop_ranging", " ").wait_for_publish()
            self.client.publish("motors/stop", " ").wait_for_publish()
            self.client.disconnect()

behavior = ObstacleAvoidingBehavior()
behavior.run()
