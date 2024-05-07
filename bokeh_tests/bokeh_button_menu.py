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
from bokeh.models import Button, CustomJS


def make_button_with_url(url, **kwargs):
    button = Button(**kwargs)
    button.js_on_click(CustomJS(code=f"window.location.href = '{url}'"))
    return button


class ManualDrive(Handler):
    def button_click(self, event: Event):
        print(f"Button clicked {event.model.name}")

    def modify_document(self, doc: Document) -> None:
        button = Button(label="Drive", name="drive", button_type="primary", sizing_mode="stretch_width")
        button.on_click(self.button_click)
        back_button = make_button_with_url("/", label="Back", name="back", button_type="warning", sizing_mode="stretch_width")
        # back_button.on_click(OpenURL(url="/", same_tab=True))

        doc.add_root(
            column(
                button,
                back_button
            )
        )
#set_curdoc is a possible way to do this.
#OpenURL only works with TapTool (documentation is a bit poor here)

class ButtonPage(Handler):
    menu_items = [
        { "url": '/manual_drive', "label": 'Manual drive' },
        { "url": '/behavior_path', "label": 'Drive path'},
        { "url": '/behavior_line', "label": 'Drive line'},
        { "url": '/distance_plotter', "label": 'Distance plotter'},
        { "url": '/bang_bang_obstacle_avoiding', "label": 'Bang Bang Obstacle Avoiding' },
        { "url": '/proportional_obstacle_avoiding', "label": 'Proportional Obstacle Avoiding' },
        { "url": '/encoder_driver', "label": 'Encoder driver' },
        { "url": '/power_off', "label": 'Power off'},
    ]

    def modify_document(self, doc: Document) -> None:
        buttons = []

        for item in self.menu_items:
            button = make_button_with_url(item['url'],label=item['label'], button_type="primary", sizing_mode="stretch_width")
            # button.on_click(OpenURL(url=item['url'], same_tab=True).trigger)
            buttons.append(button)
        doc.add_root(column(*buttons))

server = Server(
    {
        "/": Application(ButtonPage()),
        "/manual_drive": Application(ManualDrive())
    },
    port=5006,
    address="0.0.0.0",
    allow_websocket_origin=["*"],
)

server.start()
print("Server started at http://localhost:5006/")
server.run_until_shutdown()
