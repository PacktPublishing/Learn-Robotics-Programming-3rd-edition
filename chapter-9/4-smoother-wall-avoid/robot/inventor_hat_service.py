import atexit
import ujson as json
import inventorhatmini
import paho.mqtt.client as mqtt
import time

class InventorHATService:
    last_message = 0
    def __init__(self) -> None:
        self.board = inventorhatmini.InventorHATMini()
        self.left_motor = self.board.motors[1]
        self.right_motor = self.board.motors[0]
        self.client = None

        atexit.register(self.exit_handler)

    def loop_forever(self):
        self.connect()
        self.client.message_callback_add("motors/#", self.print_message)
        self.client.message_callback_add("motors/stop", self.stop_motors)
        self.client.message_callback_add("motors/left", self.set_left_motor)
        self.client.message_callback_add("motors/right", self.set_right_motor)
        self.client.message_callback_add("motors/set_both", self.set_both_motors)

        self.client.message_callback_add("leds/#", self.print_message)
        self.client.message_callback_add("leds/set", self.set_led)

        self.client.connect("localhost", 1883)
        self.board.leds.set_rgb(0, 0, 90, 0)
        while True:
            if time.time() - self.last_message > 1:
                self.stop_motors()
            self.client.loop()
            # time.sleep(0.01)

    def connect(self):
        mqtt_username = "robot"
        mqtt_password = "robot"

        self.client = mqtt.Client()
        self.client.username_pw_set(mqtt_username, mqtt_password)
        self.client.on_connect = self.on_connect

    def set_left_motor(self, client, userdata, msg):
        speed = json.loads(msg.payload)
        self.left_motor.enable()
        self.left_motor.speed(speed)
        self.last_message = time.time()

    def set_right_motor(self, client, userdata, msg):
        speed = json.loads(msg.payload)
        self.right_motor.enable()
        self.right_motor.speed(speed)
        self.last_message = time.time()

    def set_both_motors(self, client, userdata, msg):
        left_speed, right_speed = json.loads(msg.payload)
        self.left_motor.enable()
        self.right_motor.enable()
        self.left_motor.speed(left_speed)
        self.right_motor.speed(right_speed)
        self.last_message = time.time()

    def stop_motors(self, client=None, userdata=None, msg=None):
        self.left_motor.stop()
        self.right_motor.stop()

    def print_message(self, client, userdata, msg):
        print(f"{msg.topic} {msg.payload}")
        self.last_message = time.time()

    def set_led(self, client, userdata, msg):
        index, r, g, b = json.loads(msg.payload)
        self.board.leds.set_rgb(index, r, g, b)
        self.last_message = time.time()

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")
        client.subscribe("motors/#")
        client.subscribe("leds/#")

    def exit_handler(self):
        self.stop_motors()
        self.board.leds.clear()

service = InventorHATService()
service.loop_forever()
