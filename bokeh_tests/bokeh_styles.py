from bokeh.plotting import figure, show
from bokeh.models import BoxAnnotation
from bokeh.io import curdoc

# prepare some data
x = [1, 2, 3, 4, 5]
y1 = [6, 7, 2, 4, 5]
y2 = [2, 3, 4, 5, 6]
y3 = [4, 5, 5, 7, 2]
# create a new plot with a title and axis labels
p = figure(title="Multiple line example", x_axis_label='x', y_axis_label='y',
           width=600, height=800)
# add multiple renderers
line = p.line(x, y1, legend_label="Temp.", color="blue", line_width=2)
p.vbar(x=x, top=y2, legend_label="Rate", width=0.5, bottom=0, color="red")
circle = p.scatter(
    x,
    y3,
    marker="circle",
    size=80,
    legend_label="Objects",
    fill_color="red",
    fill_alpha=0.5,
    line_color="blue",
)
glyph = circle.glyph
glyph.fill_color = "green"

# apply theme to current document
curdoc().theme = "dark_minimal"

# change headline location to the left
p.title_location = "left"
# display legend in top left corner (default is top right corner)
p.legend.location = "top_left"

# add a title to your legend
p.legend.title = "Obervations"

# change appearance of legend text
p.legend.label_text_font = "times"
p.legend.label_text_font_style = "italic"
p.legend.label_text_color = "navy"

# change border and background of legend
p.legend.border_line_width = 3
p.legend.border_line_color = "navy"
p.legend.border_line_alpha = 0.8
p.legend.background_fill_color = "navy"
p.legend.background_fill_alpha = 0.2

# add box annotations
low_box = BoxAnnotation(top=2, fill_alpha=0.2, fill_color="#F0E442")
mid_box = BoxAnnotation(bottom=2, top=80, fill_alpha=0.2, fill_color="#009E73")
high_box = BoxAnnotation(bottom=6, fill_alpha=0.2, fill_color="#F0E442")
# add boxes to existing figure
p.add_layout(low_box)
p.add_layout(mid_box)
p.add_layout(high_box)
# show the results
show(p)
