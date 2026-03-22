import atexit
import time
import math
import ujson as json

from common.mqtt_behavior import connect, publish_json

TURN_SPEED_MM_PER_SEC = 180
WHEEL_DISTANCE_MM = 136 #161.0
TARGET_ROTATION_RAD = 2 * math.pi
TURN_TIMEOUT_SEC = 20


class EncoderTurnCalibration:
    def __init__(self):
        self.running = True
        self.left_distance = 0.0
        self.right_distance = 0.0
        self.client = connect()
        self.client.subscribe("sensors/encoders/data")
        self.client.message_callback_add("sensors/encoders/data", self.on_encoders_data)
        self.client.subscribe("all/stop")
        self.client.message_callback_add("all/stop", self.stop)

    def on_encoders_data(self, client, userdata, msg):
        data = msg.payload
        if isinstance(data, (bytes, bytearray)):
            data = data.decode()
        payload = json.loads(data)
        self.left_distance = payload.get("left_distance", 0.0)
        self.right_distance = payload.get("right_distance", 0.0)

    def start(self):
        print("Starting encoder turn calibration")
        publish_json(self.client, "sensors/encoders/control/reset", "")
        publish_json(self.client, "wheel_control/enabled", True)
        publish_json(
            self.client,
            "wheel_control/wheel_speed_mm",
            [-TURN_SPEED_MM_PER_SEC, TURN_SPEED_MM_PER_SEC]
        )

        start_time = time.time()
        while self.running:
            rotation_estimate = (self.right_distance - self.left_distance) / WHEEL_DISTANCE_MM
            if abs(rotation_estimate) >= TARGET_ROTATION_RAD:
                self.stop()
                break
            if time.time() - start_time > TURN_TIMEOUT_SEC:
                print("Stopping encoder turn calibration (timeout)")
                self.stop()
                break
            time.sleep(0.1)

    def stop(self, *_):
        if not self.running:
            return
        print("Stopping encoder turn calibration")
        self.running = False
        publish_json(self.client, "wheel_control/wheel_speed_mm", [0, 0])
        publish_json(self.client, "wheel_control/enabled", False)


service = EncoderTurnCalibration()

atexit.register(service.stop)

service.start()
