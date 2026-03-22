import ujson as json

from common.mqtt_behavior import connect, publish_json, subscribe
from common.pid_control import PIDController

from common.bokeh_time_plot import BokehTimePlot, make_server

# simple design
# - drive/stop: {}
# - all/stop: {}
# - drive/start {}
# - drive/set: {"k_p": 0.1, "k_i": 0.01, "k_d": 0.001}
# - drive/get: {}
## publishes
# - drive/settings: {"k_p": 0.1, "k_i": 0.01, "k_d": 0.001}
# - motors/wheels: [0.8, 0.8]
## Streams
# - Bokeh plots on port 5002

class EncoderLineDrive:
  running = False
  speed = 0.7

  def __init__(self):
    # self.pid = PIDController(0.0027, 0.0001, 0)
    self.pid = PIDController(0.0004, 0, 0)
    self.mqtt_client = None
    self.plotter = BokehTimePlot(
      ["error", "diff"],
      title="Encoder Line Drive", 
      y_axis_label="Error"
    )

  def start(self, *_):
    print("Starting...")
    self.running = True
    self.pid.reset()
    publish_json(self.mqtt_client, 
      "sensors/encoders/control", 
      {"running": True, "frequency": 50, "reset": True}
    )
    publish_json(self.mqtt_client, "motors/wheels", [self.speed, self.speed])

  def stop(self, *_):
    self.running = False
    publish_json(self.mqtt_client, "motors/wheels", [0, 0])
    publish_json(self.mqtt_client, 
      "sensors/encoders/control", 
      {"running": False}
    )

  def get_pid(self, *_):
    publish_json(self.mqtt_client, "drive/settings", {
      "k_p": self.pid.k_p,
      "k_i": self.pid.k_i,
      "k_d": self.pid.k_d
    })
  
  def set_pid(self, client, userdata, message):
    data = json.loads(message.payload)
    if "k_p" in data:
      self.pid.k_p = data["k_p"]
    if "k_i" in data:
      self.pid.k_i = data["k_i"]
    if "k_d" in data:
      self.pid.k_d = data["k_d"]

  def think(self, error, delta_time):
    return self.pid.control(error, delta_time)

  def sense(self, client, userdata, message):
    data = json.loads(message.payload)
    left_count = data["left_count"]
    right_count = data["right_count"]
    error = left_count - right_count

    if self.running:
      diff = self.think(error, data["dt"])
      self.plotter.log({
        "error": error, "diff": diff
      })
      publish_json(self.mqtt_client, "motors/wheels", [
        self.speed - diff,
        self.speed + diff
      ])

  def on_connect(self, client, userdata, flags, rc):
    subscribe(client, "drive/stop", self.stop)
    subscribe(client, "drive/start", self.start)
    subscribe(client, "drive/get", self.get_pid)
    subscribe(client, "drive/set", self.set_pid)
    subscribe(client, "all/stop", self.stop)
    subscribe(client, 
      "sensors/encoders/data", 
      self.sense
    )
    client.will_set("all/stop", payload="{}")

  def loop_forever(self):
    print("Making connection")
    self.mqtt_client = connect(self.on_connect)
    print("Starting loop")
    self.mqtt_client.loop_start()
    server = make_server(self.plotter)
    server.start()
    server.run_until_shutdown()

behavior = EncoderLineDrive()
behavior.loop_forever()
