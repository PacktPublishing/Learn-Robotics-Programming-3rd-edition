from common.mqtt_behavior import connect, publish_json, subscribe
from common.pid_control import PIController

# simple design
# - drive/stop: {}
# - stop/all: {}
# - drive/start {}
# - drive/set: {"kp": 0.1, "ki": 0.01}
# - drive/get: {}
## publishes
# - drive/error: {"error": 0.1, "dt": 0.01}
# - drive/settings: {"kp": 0.1, "ki": 0.01}
# - motors/wheels: {"left": 0.8, "right": 0.8}

class EncoderLineDrive:
  running = False
  speed = 0.8

  def __init__(self):
    self.pid = PIController(0.1, 0.01)
    self.mqtt_client = None

  def start(self):
    self.running = True
    publish_json(self.mqtt_client, 
      "sensors/encoder/control", 
      {"reset": True}
    )
    publish_json(self.mqtt_client, "motors/wheels", {
      "left": self.speed,
      "right": self.speed
    })

  def stop(self):
    self.running = False
    publish_json(self.mqtt_client, "motors/wheels", {
      "left": 0,
      "right": 0
    })

  def get_pid(self):
    publish_json(self.mqtt_client, "drive/settings", {
      "kp": self.pid.kp,
      "ki": self.pid.ki,
    })
  
  def set_pid(self, data):
    if "kp" in data:
      self.pid.kp = data["kp"]
    if "ki" in data:
      self.pid.ki = data["ki"]

  def think(self, error, delta_time):
    return self.pid.control(error, delta_time)

  def sense(self, client, userdata, message):
    data = json.loads(message.payload)
    left_count = data["left_count"]
    right_count = data["right_count"]
    diff = left_count - right_count
    error = diff
    if self.running:
      speed = self.think(error, data["dt"])
      publish_json(self.mqtt_client, "drive/error", {
        "error": error,
        "dt": data["dt"]
      })
      publish_json(self.mqtt_client, "motors/wheels", {
        "left": speed,
        "right": speed
      })

  def on_connect(self, client, userdata, flags, rc):
    subscribe(client, "drive/stop", self.stop)
    subscribe(client, "drive/start", self.start)
    subscribe(client, "drive/get", self.get_pid)
    subscribe(client, "drive/set", self.set_pid)
    subscribe(client, "stop/all", self.stop)
    subscribe(client, 
      "sensors/encoders/data", 
      self.sense
    )

  def loop_forever(self):
    print("Making connection")
    self.mqtt_client = connect(self.on_connect)
    print("Starting loop")
    self.mqtt_client.loop_forever()

behavior = EncoderLineDrive()
behavior.loop_forever()
# not tested. tomorrow we test it.