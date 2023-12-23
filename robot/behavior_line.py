import time
from robot.mqtt_behavior import connect

client = connect()
client.publish("motors/left", 0.8)
client.publish("motors/right", 0.8)
time.sleep(2)
client.publish("motors/stop", "")
client.loop_stop()
