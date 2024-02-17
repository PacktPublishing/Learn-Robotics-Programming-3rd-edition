import numpy as np
import ujson as json
from bokeh.plotting import figure
from bokeh.server.server import Server
from bokeh.application import Application
from bokeh.application.handlers.function import FunctionHandler
from bokeh.plotting import figure, ColumnDataSource
from bokeh.document import Document

from common.mqtt_behavior import connect


class SensorData:
    def __init__(self):
        self.data = np.zeros((8, 8))

    def data_received(self, client, userdata, msg):
        self.data = json.loads(msg.payload)

    def start(self):
        client = connect(start_loop=False)
        client.loop_start()
        client.subscribe("sensors/distance_mm")
        client.message_callback_add("sensors/distance_mm", self.data_received)


sensor_data = SensorData()

def make_display(doc: Document):
    source = ColumnDataSource({'image': []})
    def update():
        clipped = np.clip(sensor_data.data, 1, None)
        transformed = np.flipud(np.log(clipped))

        source.data = {'image': [transformed]}

    doc.add_periodic_callback(update, 50)
    fig = figure(title="Distance sensor data", x_axis_label="x", y_axis_label="y")
    fig.image(source=source, x=0, y=0, dw=8, dh=8, palette="Greys256")
    doc.add_root(fig)

print("Starting plotter")
sensor_data.start()
apps = {'/': Application(FunctionHandler(make_display))}

server = Server(apps, port=5000, address="0.0.0.0", allow_websocket_origin=["learnrob3.local:5000"])
server.start()
server.run_until_shutdown()
