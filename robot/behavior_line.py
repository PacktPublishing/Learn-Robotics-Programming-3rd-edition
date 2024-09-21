from time import sleep
from common.mqtt_behavior import connect, publish_json

client = connect()
publish_json(client, "motors/wheels", [0.8, 0.8])
sleep(1)
publish_json(client, "motors/wheels", [0.8, 0.8])
sleep(1)
