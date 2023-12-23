from time import sleep
from mqtt_behavior import connect

client = connect()
client.publish("motors/left", 0.8)
client.publish("motors/right", 0.8)
sleep(2)
client.publish("motors/stop", "")
client.loop_stop()
