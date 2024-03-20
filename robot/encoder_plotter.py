import ujson as json
from bokeh.server.server import Server
from bokeh.application import Application
from bokeh.application.handlers.handler import Handler
from bokeh.plotting import figure, ColumnDataSource
from bokeh.document import Document
# TODO: Make time into an X-axis
from common.mqtt_behavior import connect


class EncoderPlotter(Handler):
    def __init__(self):
        super().__init__()
        self.left_data = []
        self.right_data = []
        self.timestamps = []

    def data_received(self, client, userdata, msg):
        data = json.loads(msg.payload)
        self.left_data.append(data['left_distance'])
        self.right_data.append(data['right_distance'])
        self.timestamps.append(data['timestamp'])

    def start_mqtt(self):
        client = connect(start_loop=False)
        client.loop_start()
        client.subscribe("sensors/encoders/data")
        client.subscribe("sensors/encoders/control")
        client.message_callback_add("sensors/encoders/data", self.data_received)
        client.message_callback_add("sensors/encoders/control", self.control_received)
    
    def control_received(self, client, userdata, msg):
        data = json.loads(msg.payload)
        if data.get('reset') == True:
            self.left_data = []
            self.right_data = []
            self.timestamps = []
    
    def modify_document(self, doc: Document) -> None:
        column_source = ColumnDataSource({'left': [], 'right': [], 'timestamps': []})
        def update():
            column_source.data = {
                'left': self.left_data, 
                'right': self.right_data, 
                'timestamps': self.timestamps}
        doc.add_periodic_callback(update, 50)
        fig = figure(title="Encoder data", x_axis_label="time", y_axis_label="mm")
        fig.line('timestamps', 'left', source=column_source, line_width=2, line_color='red')
        fig.line('timestamps', 'right', source=column_source, line_width=2, line_color='blue')
        doc.add_root(fig)


print("Starting plotter")
encoder_plotter = EncoderPlotter()
encoder_plotter.start_mqtt()
apps = {'/': Application(encoder_plotter)}

server = Server(apps, port=5001, address="0.0.0.0", allow_websocket_origin=["learnrob3.local:5001"])
server.start()
server.run_until_shutdown()
