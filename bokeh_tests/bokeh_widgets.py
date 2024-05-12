from bokeh.layouts import layout
from bokeh.plotting import figure, show
from bokeh.io import curdoc
from bokeh.models import Div, RangeSlider, Spinner

x = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
y = [4, 5, 5, 7, 2, 6, 4, 9, 1, 3]

p = figure(x_range=(1,9), width=500, height=250)
points = p.scatter(x=x, y=y, size=30, fill_color="#21a7df")

div = Div(
    text="""
        <p>Select the circle's size using this control element:</p>
        """,
    width=200,
    height=30,
)

spinner = Spinner(
    title="Circle size",  # a string to display above the widget
    low=0,  # the lowest possible number to pick
    high=60,  # the highest possible number to pick
    step=5,  # the increments by which the number can be adjusted
    value=points.glyph.size,  # the initial value to display in the widget
    width=200,  #  the width of the widget in pixels
)

spinner.js_link("value", points.glyph, "size")

range_slider = RangeSlider(
    title="Adjust x-axis range", # a title to display above the slider
    start=0,  # set the minimum value for the slider
    end=10,  # set the maximum value for the slider
    step=1,  # increments for the slider
    value=(p.x_range.start, p.x_range.end),  # initial values for slider
)

range_slider.js_link("value", p.x_range, "start", attr_selector=0)
range_slider.js_link("value", p.x_range, "end", attr_selector=1)

# apply theme to current document
curdoc().theme = "dark_minimal"

layout = layout([
    [div, spinner],
    [range_slider],
    [p],
])

# put the results in a column and show
show(layout)
