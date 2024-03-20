import atexit
import json
from threading import Thread
import time
import inventorhatmini
import paho.mqtt.client as mqtt

last_message = 0
board = inventorhatmini.InventorHATMini()
left_motor = board.motors[1]
right_motor = board.motors[0]
left_encoder = board.encoders[1]
right_encoder = board.encoders[0]
# Settings for FIT0450 motors
# Gear ratio: 120:1
# Counts per rev: 8
left_encoder.counts_per_rev(8 * 120)
right_encoder.counts_per_rev(8 * 120)

# WARNING: Using these with the motors may need external power. I recommend two 18650 battery for this.
# You will want suitable charging, and a battery that has protection.
pan_servo = board.servos[inventorhatmini.SERVO_1]
tilt_servo = board.servos[inventorhatmini.SERVO_2]
pan_servo.disable()
tilt_servo.disable()


def all_messages(client, userdata, msg):
    global last_message
    last_message = time.time()
    print(f"{msg.topic} {msg.payload}")


def set_motor_wheels(client, userdata, msg):
    left, right = json.loads(msg.payload)
    left_motor.enable()
    left_motor.speed(left)
    right_motor.enable()
    right_motor.speed(right)


def stop_motors(client=None, userdata=None, msg=None):
    left_motor.stop()
    right_motor.stop()
    pan_servo.disable()
    tilt_servo.disable()


def set_servos(client, userdata, msg):
    data = json.loads(msg.payload)
    if "pan" in data:
        if data["pan"] == "disable":
            pan_servo.disable()
        else:
            pan_servo.value(pan_servo.mid_value() + data["pan"])
    if "tilt" in data:
        if data["tilt"] == "disable":
            tilt_servo.disable()
        else:
            tilt_servo.value(tilt_servo.mid_value() + data["tilt"])


def set_led(client, userdata, msg):
    index, r, g, b = json.loads(msg.payload)
    board.leds.set_rgb(index, r, g, b)


class EncoderMonitor(Thread):
    update_frequency = 0.1
    running = False

    def run(self):
        while True:
            if self.running:
                # https://github.com/pimoroni/ioe-python/blob/master/docs/encoder.md
                l_capture = left_encoder.capture()
                r_capture = right_encoder.capture()
                data = {
                    "left_delta": l_capture.radians_delta,
                    "right_delta": r_capture.radians_delta,
                    "left_radians": l_capture.radians,
                    "right_radians": r_capture.radians,
                }
                client.publish("sensors/encoders/data", json.dumps(data))
            time.sleep(self.update_frequency)

    def mqtt_control(self, client, userdata, msg):
        data = json.loads(msg.payload)
        if 'running' in data:
            self.running = data['running']
        if 'frequency' in data:
            self.update_frequency = data['frequency']


def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe("motors/#")
    client.subscribe("leds/#")
    client.subscribe("all/#")
    client.subscribe("sensors/encoders/control")

def all_stop(client=None, userdata=None, msg=None):
    stop_motors()
    encoder_monitor.running = False

def exit_handler():
    all_stop()
    board.leds.clear()

atexit.register(exit_handler)

encoder_monitor = EncoderMonitor()
encoder_monitor.start()

mqtt_username = "robot"
mqtt_password = "robot"

client = mqtt.Client()
client.username_pw_set(mqtt_username, mqtt_password)
client.on_connect = on_connect

client.message_callback_add("motors/#", all_messages)
client.message_callback_add("motors/stop", stop_motors)
client.message_callback_add("motors/wheels", set_motor_wheels)
client.message_callback_add("motors/servos", set_servos)
client.message_callback_add("leds/#", all_messages)
client.message_callback_add("leds/set", set_led)
client.message_callback_add("all/stop", all_stop)
client.message_callback_add("sensors/encoders/control", encoder_monitor.mqtt_control)

client.connect("localhost", 1883)
board.leds.set_rgb(0, 0, 90, 0)
client.loop_start()
while True:
    if time.time() - last_message > 1:
        stop_motors()
    time.sleep(0.1)
