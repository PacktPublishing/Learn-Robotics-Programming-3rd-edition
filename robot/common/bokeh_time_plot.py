from typing import List
import time

import numpy as np
from bokeh.server.server import Server
from bokeh.application import Application
from bokeh.application.handlers.handler import Handler
from bokeh.plotting import figure, ColumnDataSource
from bokeh.document import Document


class BokehTimePlot(Handler):
    """Graph and log data"""
    color_names = ['red', 'green', 'blue', 'purple', 'orange', 'black']
    plot_points = 400

    def __init__(self, column_names: List[str], title="Time Plot", y_axis_label="y"):
        super().__init__()
        self.column_names = column_names
        self.data = {name: np.zeros(self.plot_points) for name in column_names}
        self.start_time = time.time()
        self.timestamps = np.zeros(self.plot_points)
        self.title = title
        self.y_axis_label = y_axis_label

    def log(self, data):
        for name in self.column_names:
            if name in data:
                self.data[name] = np.roll(self.data[name], 1)
                self.data[name][0] = data[name]
        self.timestamps = np.roll(self.timestamps, 1)
        self.timestamps[0] = time.time() - self.start_time
    
    def modify_document(self, doc: Document) -> None:
        column_source = ColumnDataSource({name: [] for name in self.column_names} | {'timestamps': []})
        def update():
            column_source.data = {
                name: self.data[name] for name in self.column_names
            } | {'timestamps': self.timestamps}
        doc.add_periodic_callback(update, 50)
        fig  = figure(title=self.title, x_axis_label="time", y_axis_label=self.y_axis_label)
        for name, color in zip(self.column_names, self.color_names):
            fig.line('timestamps', name, legend_label=name, source=column_source, line_width=2, line_color=color)

        doc.add_root(fig)

def make_server(plot: BokehTimePlot):
    apps = {'/': Application(plot)}
    return Server(apps, port=5002, address="0.0.0.0", allow_websocket_origin=["*"])
