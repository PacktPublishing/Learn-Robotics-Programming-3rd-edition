import time
import numpy as np
import ujson as json
from bokeh.server.server import Server
from bokeh.application import Application
from bokeh.application.handlers.handler import Handler
from bokeh.plotting import figure, ColumnDataSource
from bokeh.models import Range1d

from common.mqtt_behavior import connect, publish_json


class BangBangObstacleAvoidingBehavior:
    def __init__(self):
        self.speed = 0.6
        self.left_distance = 0
        self.right_distance = 0
        self.threshold = 300

    def on_distance_message(self, client, userdata, message):
        # Sense
        sensor_data = np.array(json.loads(message.payload))
        grid = np.fliplr(sensor_data.reshape((8, 8)))
        top_lines = grid[4:, :]
        left_sensors = top_lines[:, :2]
        right_sensors = top_lines[:, -2:]
        self.left_distance = int(np.min(left_sensors))
        self.right_distance = int(np.min(right_sensors))
        # print(f"Left: {self.left_distance}, Right: {self.right_distance}")

        # Think
        left_motor_speed = self.speed
        right_motor_speed = self.speed
        if self.left_distance < self.threshold:
            right_motor_speed = -self.speed
        elif self.right_distance < self.threshold:
            left_motor_speed = -self.speed

        # Act
        publish_json(client, "motors/wheels", [left_motor_speed, right_motor_speed])

    def start_mqtt(self):
        client = connect(start_loop=False)
        client.subscribe("sensors/distance_mm")
        client.message_callback_add("sensors/distance_mm", self.on_distance_message)
        client.publish("sensors/distance/control/start_ranging", "")
        client.publish("behavior/bang_bang_obstacle_avoider", "ready")
        client.loop_start()


class BangBangMonitor(Handler):
    def __init__(self, behavior):
        super().__init__()
        self.behavior = behavior

    def modify_document(self, doc):
        # Let's make a data source time series - time vs left and right distance
        column_source = ColumnDataSource(
            {
                "time": np.full(100, time.time(), dtype=np.datetime64),
                "left_distance": np.zeros(100),
                "right_distance": np.zeros(100),
            }
        )

        def update():
            column_source.stream(
                {
                    "time": np.array([time.time()], dtype=np.datetime64),
                    "left_distance": [self.behavior.left_distance],
                    "right_distance": [self.behavior.right_distance],
                }
            )

        doc.add_periodic_callback(update, 50)
        fig = figure(max_width=200, max_height=200, x_axis_type="datetime")
        fig.line(source=column_source, x="time", y="left_distance", line_color="red")
        fig.line(source=column_source, x="time", y="right_distance", line_color="blue")
    # Add the threshold line, make it dashed and green
        fig.line(
            x=[0, 1],
            y=[self.behavior.threshold, self.behavior.threshold],
            line_color="green",
            line_dash="dashed",
        )
        fig.x_range = Range1d(time.time() - 10, time.time() + 10)
        doc.add_root(fig)


behavior = BangBangObstacleAvoidingBehavior()
behavior.start_mqtt()
monitor = BangBangMonitor(behavior)
apps = {"/": Application(monitor)}

server = Server(
    apps,
    port=5001,
    prefix="/bang_bang_obstacle_avoider_plot/",
    address="0.0.0.0",
    allow_websocket_origin=["learnrob3.local"],
)
server.start()
server.run_until_shutdown()
