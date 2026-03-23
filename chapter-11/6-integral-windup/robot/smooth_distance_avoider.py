import time
import numpy as np
import ujson as json
from bokeh.server.server import Server
from bokeh.application import Application
from bokeh.application.handlers.handler import Handler
from bokeh.plotting import figure, ColumnDataSource

from common.mqtt_behavior import connect, publish_json


class SmoothDistanceAvoiderBehavior:
    def __init__(self):
        self.speed = 0.6
        self.left_distance = 0
        self.right_distance = 0
        self.curve_proportion = 30

    def on_distance_message(self, client, userdata, message):
        # Sense
        sensor_data = np.array(json.loads(message.payload))
        grid = np.fliplr(sensor_data.reshape((8, 8)))
        top_lines = grid[4:, :]
        left_sensors = top_lines[:, :2]
        right_sensors = top_lines[:, -2:]
        self.left_distance = int(np.min(left_sensors))
        self.right_distance = int(np.min(right_sensors))

        # Think
        nearest_distance = min(self.left_distance, self.right_distance)
        inverse = 1/max(nearest_distance, 1)
        self.curve = self.curve_proportion * inverse

        furthest_speed = np.clip(self.speed - self.curve, -1, 1)
        nearest_speed = np.clip(self.speed + self.curve, -1, 1)

        if self.left_distance < self.right_distance:
            left_motor_speed = nearest_speed
            right_motor_speed = furthest_speed
        else:
            left_motor_speed = furthest_speed
            right_motor_speed = nearest_speed

        # Act
        publish_json(client, "motors/wheels", [left_motor_speed, right_motor_speed])

    def start(self):
        client = connect(start_loop=False)
        client.subscribe("sensors/distance_mm")
        client.message_callback_add("sensors/distance_mm", self.on_distance_message)
        client.publish("sensors/distance/control/start_ranging", "")
        client.loop_start()


class SmoothDistanceMonitor(Handler):
    def __init__(self, behavior):
        super().__init__()
        self.behavior = behavior

    def modify_document(self, doc):
        # Let's make a data source time series - time vs left and right distance
        column_source = ColumnDataSource(
            {
                "time": [],
                "left_distance": [],
                "right_distance": [],
            }
        )
        start_time = time.time()

        def update():
            column_source.stream(
                {
                    "time": [time.time() - start_time],
                    "left_distance": [self.behavior.left_distance],
                    "right_distance": [self.behavior.right_distance],
                }
            )

        doc.add_periodic_callback(update, 50)
        fig = figure(max_width=200, max_height=200)
        fig.line(source=column_source, x="time", y="left_distance", line_color="red")
        fig.line(source=column_source, x="time", y="right_distance", line_color="blue")
        # Add the threshold line, make it dashed and green
        fig.ray(
            x=[0], y=[self.behavior.curve_proportion],
            length=0, angle=0,
            line_color="green", line_dash="dashed",
        )
        doc.add_root(fig)


behavior = SmoothDistanceAvoiderBehavior()
monitor = SmoothDistanceMonitor(behavior)
apps = {"/": Application(monitor)}

server = Server(
    apps,
    port=5002,
    prefix="/smooth_distance_avoider_plot/",
    address="0.0.0.0",
    allow_websocket_origin=["learnrob3.local"],
)
server.start()
behavior.start()
server.run_until_shutdown()
