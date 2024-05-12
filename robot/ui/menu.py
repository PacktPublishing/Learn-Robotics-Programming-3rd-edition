import socket

from bokeh.document import Document
from bokeh.models import Div, Button, CustomJS, OpenURL
from bokeh.layouts import column
from bokeh.application.handlers.handler import Handler

from bokeh.server.server import Server
from bokeh.application import Application

menu_items = [
    {"link": "/manual_drive", "label": "Manual drive"},
    {"link": "/behavior_path", "label": "Drive path"}
]


class Menu(Handler):
    def modify_document(self, doc: Document):
        col = column()
        col.children.append(
            Div(text="<h1>Robot control</h1>")
        )
        for item in menu_items:
            button = Button(
                    label=item["label"], 
                    button_type="primary", 
                    sizing_mode="stretch_width"
                )
            button.js_on_click(
                CustomJS(code=f"window.location.href = '{item['link']}'")
            )
            col.children.append(button)
        doc.add_root(col)


server = Server(
    {"/": Application(Menu())},
    port=5006,
    address="0.0.0.0",
    allow_websocket_origin=["*"],
)
server.start()
print(f"Server started at http://{socket.gethostname()}:5006/")
server.run_until_shutdown()
