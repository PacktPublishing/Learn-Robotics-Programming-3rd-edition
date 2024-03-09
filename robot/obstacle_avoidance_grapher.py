import numpy as np
import ujson as json
from bokeh.plotting import figure
from bokeh.server.server import Server
from bokeh.application import Application
from bokeh.application.handlers.handler import Handler
from bokeh.plotting import figure, ColumnDataSource
from bokeh.document import Document

from common.mqtt_behavior import connect


"""Intention:
Make live graphs screen of distance vs motors.
Distance graphs -> 0 to 300 mm far.
Motors -> -1 to 1
Have graphs for the left/right. Such that the distance is above the motor response over time.
As data arrives from MQTT, add it to the graph.
"""

class ObstacleAvoidanceGrapher(Handler):
    def __init__(self):
        super().__init__()
        self.data = np.zeros((8, 8))

    def data_received(self, client, userdata, msg):
        self.data = json.loads(msg.payload)

    def start_mqtt(self):
        client = connect(start_loop=False)
        client.loop_start()
        client.subscribe("log/obstacle_avoider")
        client.message_callback_add("log/obstacle_avoider", self.data_received)

    def modify_document(self, doc: Document):
        column_source = ColumnDataSource({'image': []})
        
        def update():
            clipped = np.clip(self.data, 1, None)
            transformed = np.flipud(np.log(clipped))
            column_source.data = {'image': [transformed]}

        doc.add_periodic_callback(update, 50)
        fig = figure(title="Distance sensor data", x_axis_label="x", y_axis_label="y")
        fig.image(source=column_source, x=0, y=0, dw=8, dh=8, palette="Greys256")
        doc.add_root(fig)
    

print("Starting plotter")
distance_plotter = ObstacleAvoidanceGrapher()
distance_plotter.start_mqtt()
apps = {'/': Application(distance_plotter)}

server = Server(apps, port=5001, address="0.0.0.0", allow_websocket_origin=["learnrob3.local:5001"])
server.start()
server.run_until_shutdown()
