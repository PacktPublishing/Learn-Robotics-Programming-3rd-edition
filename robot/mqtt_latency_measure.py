import time

import ujson as json

from common.mqtt_behavior import connect, publish_json, subscribe

class MeasureMqttLatency:
    """
    Uses MQTT to measure the latency of the system.
    Sends a message with a timestamp in millis, and receives it back.
    Compares the timestamp it sent with the timestamp it received.
    Prints the difference.
    """
    def __init__(self) -> None:
        self.mqtt_client = None

    def send_latency(self):
        send_timestamp = time.monotonic_ns()
        publish_json(self.mqtt_client, "latency", {"timestamp": send_timestamp})

    def on_latency(self, client, userdata, message):
        data = json.loads(message.payload)
        received_at = time.monotonic_ns()
        received_timestamp = data["timestamp"]
        latency = received_at - received_timestamp
        print(f"Latency: {latency}ns")

    def start(self, *_):
        self.mqtt_client = connect()
        subscribe(self.mqtt_client, "latency", self.on_latency)
        self.mqtt_client.loop_start()
        while True:
            self.send_latency()
            time.sleep(0.1)

behavior = MeasureMqttLatency()
behavior.start()
# Latency is 582,333.4211 nanoseconds - less than 1 ms. Even with a round trip, this is very fast.
# Motor response/encoder response time is the larger factor then, that and any loop times or processing.