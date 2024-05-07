## Things to try:
# - a set of buttons in a column
# - Pages - loading different graphs
# - Delegating parts to another page source (another bokeh service?)

from bokeh.document import Document
from bokeh.server.server import Server
from bokeh.application import Application
from bokeh.application.handlers.handler import Handler

from bokeh.events import Event

from bokeh.layouts import column
from bokeh.models import Button

class ButtonPage(Handler):
    menu_items = [
        { "name": 'manual_drive', "label": 'Manual drive' },
        { "name": 'behavior_path', "label": 'Drive path'},
        { "name": 'behavior_line', "label": 'Drive line'},
        { "name": 'distance_plotter', "label": 'Distance plotter'},
        { "name": 'bang_bang_obstacle_avoiding', "label": 'Bang Bang Obstacle Avoiding' },
        { "name": 'proportional_obstacle_avoiding', "label": 'Proportional Obstacle Avoiding' },
        { "name": 'encoder_driver', "label": 'Encoder driver' },
        { "name": 'power_off', "label": 'Power off'},
    ]

    def button_click(self, event: Event):
        print(f"Button clicked {event.model.name}")

    def modify_document(self, doc: Document) -> None:
        buttons = []

        for item in self.menu_items:
            button = Button(label=item['label'], name=item["name"], button_type="primary", sizing_mode="stretch_width")
            button.on_click(self.button_click)
            buttons.append(button)
        doc.add_root(column(*buttons))

server = Server(
    {"/": Application(ButtonPage())},
    port=5006,
    address="0.0.0.0",
    allow_websocket_origin=["*"],
)

server.start()
print("Server started at http://localhost:5006/")
server.run_until_shutdown()
