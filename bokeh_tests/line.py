import numpy as np
from bokeh.server.server import Server
from bokeh.application import Application
from bokeh.application.handlers.function import FunctionHandler
from bokeh.plotting import figure, ColumnDataSource

theta = 0

def make_document(doc):
    source = ColumnDataSource({'x': [], 'y': []})
    def update():
        global theta

        x = np.linspace(0, 4 * np.pi, 100)
        y = np.sin(x + theta)
        theta += np.pi / 100
        source.data = {'x': x, 'y': y}

    try:
        doc.add_periodic_callback(update, 50)
        fig = figure(title="simple line example", x_axis_label="x", y_axis_label="y")
        fig.line('x', 'y', source=source, line_width=2)
        doc.add_root(fig)
    except Exception as e:
        print(e)

apps = {'/': Application(FunctionHandler(make_document))}

server = Server(apps, port=8050)
server.start()
server.run_until_shutdown()
