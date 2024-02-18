import numpy as np
from bokeh.server.server import Server
from bokeh.application import Application
from bokeh.application.handlers.function import FunctionHandler
from bokeh.plotting import figure, ColumnDataSource, show

theta = 0

source = ColumnDataSource({'image': []})
N = 500
x = np.linspace(0, 10, N)
y = np.linspace(0, 10, N)
xx, yy = np.meshgrid(x, y)
d = np.sin(xx)*np.cos(yy)
source.data = {'image': [d]}

fig = figure(title="simple line example", x_axis_label="x", y_axis_label="y")
fig.image(source=source, x=0, y=0, dw=10, dh=10, palette="Greys256") #, level="image")
show(fig)
