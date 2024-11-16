import numpy as np
import ujson as json
from bokeh.server.server import Server
from bokeh.application import Application
from bokeh.application.handlers.handler import Handler
from bokeh.plotting import figure, ColumnDataSource

from common.mqtt_behavior import connect


class DistancePlotter(Handler):
    def __init__(self):
        super().__init__()
        self.data = np.zeros((64))

    def data_received(self, client, userdata, msg):
        self.data = json.loads(msg.payload)

    def start_mqtt(self):
        client = connect(start_loop=False)
        client.loop_start()
        client.subscribe("sensors/distance_mm")
        client.message_callback_add("sensors/distance_mm", self.data_received)

    def modify_document(self, doc):
        column_source = ColumnDataSource({'image': []})

        def update():
            clipped = np.maximum(self.data, 1)
            transformed = np.log(clipped)
            grid = np.fliplr(transformed.reshape((8, 8)))
            column_source.data['image'] = [grid]

        doc.add_periodic_callback(update, 50)
        fig = figure(max_width=250, max_height=250)
        fig.image(source=column_source, x=0, y=0, dw=8, dh=8,
                  palette="Greys256")
        doc.add_root(fig)


print("Starting plotter")
distance_plotter = DistancePlotter()
distance_plotter.start_mqtt()
apps = {'/': Application(distance_plotter)}

server = Server(apps, port=5000, prefix='/distance_plotter/',
                address="0.0.0.0",
                allow_websocket_origin=["learnrob3.local"])
server.start()
server.run_until_shutdown()
