## Things to try:
# - a set of buttons in a column
# - Pages - loading different graphs
# - Delegating parts to another page source (another bokeh service?)

from bokeh.document import Document
from bokeh.server.server import Server
from bokeh.application import Application
from bokeh.application.handlers.handler import Handler

from bokeh.plotting import figure

from bokeh.layouts import column
from bokeh.models import ColumnDataSource, Button

class ButtonPage(Handler):
    def button_click(self):
        print("Button clicked")

    def modify_document(self, doc: Document) -> None:
        button = Button(label="Click me")
        button.on_click(self.button_click)
        doc.add_root(column(button))

server = Server(
    {"/": Application(ButtonPage())},
    port=5006,
    address="0.0.0.0",
    allow_websocket_origin=["*"],
)

server.start()
print("Server started at http://localhost:5006/")
server.run_until_shutdown()
