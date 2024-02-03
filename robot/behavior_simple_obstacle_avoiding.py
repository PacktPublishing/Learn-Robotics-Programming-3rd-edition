from time import sleep
import mqtt_behavior
import numpy as np
import ujson as json

class ObstacleAvoidingBehavior:
    def __init__(self):
        self.sensor_data = None
        self.speed = 0.6

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")
        client.subscribe("sensors/distance_mm")
        client.message_callback_add("sensors/distance_mm", self.data_received)
        client.publish("sensors/distance/control/start_ranging", " ")

    def data_received(self, client, userdata, msg):
        self.sensor_data = json.loads(msg.payload)

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
        left_motor_speed = self.speed
        right_motor_speed = self.speed
        if left_distance < 300:
            right_motor_speed = -self.speed
        elif right_distance < 300:
            left_motor_speed = -self.speed
        # right_motor_speed = self.get_motor_speed(left_distance)
        # left_motor_speed = self.get_motor_speed(right_distance)
        print(left_distance,right_distance,left_motor_speed,right_motor_speed)
        self.client.publish("log/obstacle_avoiding/distances", json.dumps([left_distance,right_distance,left_motor_speed,right_motor_speed]))
        self.client.publish("motors/set_both", json.dumps([left_motor_speed, right_motor_speed]))

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
