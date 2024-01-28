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
        try:
            self.sensor_data = json.loads(msg.payload)
        except Exception as err:
            print("Error:", err)
            print("Payload:", msg.payload)

    def get_motor_speed(self, distance_mm):
        # Handle 0 - special case, usually means no data.
        if distance_mm > 0 and distance_mm < 300:
            return -self.speed
        else:
            return self.speed

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
                top_8_lines = as_array[:6, :]
                left_buckets = top_8_lines[:, :2]
                right_buckets = top_8_lines[:, -2:]
                # The distance is the minimum distance in each bucket.
                left_distance = int(np.min(left_buckets))
                right_distance = int(np.min(right_buckets))
                # print(f"[{left_distance},{right_distance}]")
                left_motor_speed = self.get_motor_speed(left_distance)
                right_motor_speed = self.get_motor_speed(right_distance)
                print(left_distance,right_distance,left_motor_speed,right_motor_speed)
                client.publish("log/obstacle_avoiding/distances", json.dumps([left_distance,right_distance,left_motor_speed,right_motor_speed]))
                client.publish("motors/set_both", json.dumps([left_motor_speed, right_motor_speed]))
        except KeyboardInterrupt:
            print("Stop requested")
        finally:
            print("Sending stop messages")
            client.publish("sensors/distance/control/stop_ranging", " ").wait_for_publish()
            client.publish("motors/stop", " ").wait_for_publish()
            client.disconnect()

behavior = ObstacleAvoidingBehavior()
behavior.run()
