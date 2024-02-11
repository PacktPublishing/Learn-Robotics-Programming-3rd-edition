from time import sleep
import json
from common.mqtt_behavior import connect

client = connect()
client.publish("motors/wheels", json.dumps([0.8, 0.8]))
sleep(2)
client.publish("motors/stop", "")
client.loop_stop()
