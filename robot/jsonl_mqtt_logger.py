"""Listener helper, log all the mqtt stuff to a jsonl file"""
from time import time
import ujson as json

from common.mqtt_behavior import connect, subscribe


class JsonLogger:
    def __init__(self):
        self.file = open("mqtt_log.jsonl", "a+")

    def log(self, client, userdata, msg):
        timestamp = time()
        data = {
            "timestamp": timestamp,
            "topic": msg.topic,
        }
        try:
            data['json_payload'] = json.loads(msg.payload)
        except ValueError:
            data['raw_payload'] = msg.payload.decode()
        self.file.write(json.dumps(data) + "\n")

    def on_connect(self, client, userdata, flags, rc):
        subscribe(client, "behavior/log/#", self.log)
        subscribe(client, "sensors/encoders/#", self.log)
        subscribe(client, "drive/#", self.log)
        subscribe(client, "all/stop", self.log)
        subscribe(client, "motors/#", self.log)

    def run(self):
        client = connect(self.on_connect, start_loop=False)
        client.loop_forever()


if __name__ == "__main__":
    JsonLogger().run()
