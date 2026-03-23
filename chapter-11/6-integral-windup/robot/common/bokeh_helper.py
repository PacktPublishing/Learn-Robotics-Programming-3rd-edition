import queue
import time

from bokeh.server.server import Server
from bokeh.application import Application
from bokeh.plotting import ColumnDataSource
from bokeh.application.handlers.handler import Handler


class PlotData:
    def __init__(self, column_names):
        self.column_names = column_names
        self.queue = queue.Queue()
        self.column_source = ColumnDataSource(
            {name: [] for name in column_names}
        )
        self.start_time = time.time()

    def put(self, data):
        self.queue.put(data)

    def update(self):
        while not self.queue.empty():
            data = self.queue.get()
            structure = {name: [data[index]]
                         for index, name in enumerate(self.column_names)}
            if 'time' in self.column_names:
                structure['time'] = [time.time() - self.start_time]
            self.column_source.stream(structure)


class QueueHandler(Handler):
    def __init__(self, plot_data, setup_plot):
        super().__init__()
        self.plot_data = plot_data
        self.setup_plot = setup_plot

    def modify_document(self, doc):
        doc.add_periodic_callback(self.plot_data.update, 50)
        doc = self.setup_plot(doc, self.plot_data.column_source)


def start_plot(plot_data, setup_plot):
    handler = QueueHandler(plot_data, setup_plot)
    apps = {'/': Application(handler)}
    server = Server(
        apps,
        port=5003,
        prefix="/behavior_plot/",
        address='0.0.0.0',
        allow_websocket_origin=['learnrob3.local'],
        )

    server.start()
    server.run_until_shutdown()
