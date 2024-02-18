import numpy as np
from bokeh.server.server import Server
from bokeh.application import Application
from bokeh.application.handlers.function import FunctionHandler
from bokeh.plotting import figure, ColumnDataSource
from bokeh.document import Document

theta = 0
zeta = 0

def make_document(doc: Document):
    source = ColumnDataSource({'image': []})
    N = 500
    x = np.linspace(0, 10, N)
    y = np.linspace(0, 10, N)
    xx, yy = np.meshgrid(x, y)
    def update():
        global theta
        global zeta
        d = np.sin(xx+theta)*np.cos(yy+zeta)
        theta += np.pi / 100
        zeta += np.pi / 300
        source.data = {'image': [d]}

    try:
        doc.add_periodic_callback(update, 50)
        fig = figure(title="simple line example", x_axis_label="x", y_axis_label="y")
        fig.image(source=source, x=0, y=0, dw=10, dh=10, palette="Greys256")
        doc.add_root(fig)
    except Exception as e:
        print(e)

apps = {'/': Application(FunctionHandler(make_document))}

server = Server(apps, port=8050)
server.start()
server.run_until_shutdown()
