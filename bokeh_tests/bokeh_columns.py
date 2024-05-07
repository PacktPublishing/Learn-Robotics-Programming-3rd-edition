from bokeh.layouts import column
from bokeh.plotting import figure, show
from bokeh.io import curdoc

# prepare some data
x = list(range(11))
y0 = x
y1 = [10 - i for i in x]
y2 = [abs(i - 5) for i in x]

# create three plots with one renderer each
s1 = figure(width=250, height=250, background_fill_color="#fafafa")
s1.scatter(x, y0, marker="circle", size=12, color="#53777a", alpha=0.8)

s2 = figure(width=250, height=250, background_fill_color="#fafafa")
s2.scatter(x, y1, marker="triangle", size=12, color="#c02942", alpha=0.8)

s3 = figure(width=250, height=250, background_fill_color="#fafafa")
s3.scatter(x, y2, marker="square", size=12, color="#d95b43", alpha=0.8)

# apply theme to current document
curdoc().theme = "dark_minimal"

# put the results in a column and show
show(column(s1, s2, s3))
