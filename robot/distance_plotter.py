import quart
import asyncio
import json
import io
import numpy as np
import matplotlib.pyplot as plt
import paho.mqtt.client as mqtt


class DistancePlotter:
    def __init__(self) -> None:
        self.make_plot(np.zeros((8, 8)))

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")
        client.subscribe("sensors/distance_mm")
        client.message_callback_add("sensors/distance_mm", self.update_plot)

    def connect(self):
        mqtt_username = "robot"
        mqtt_password = "robot"

        client = mqtt.Client()
        client.username_pw_set(mqtt_username, mqtt_password)
        client.on_connect = self.on_connect
        client.connect("localhost", 1883)
        return client

    def make_plot(self, data):
        as_array = np.array(data)
        as_array = np.clip(as_array, 0, 300)
        fig = plt.Figure()
        ax = fig.subplots()
        # ax.plot(as_array[0], range(8))
        ax.imshow(as_array, cmap="gray")
        img = io.BytesIO()
        fig.savefig(img, format="png")
        self.frame = img.getbuffer()

    def update_plot(self, client, userdata, msg):
        data = json.loads(msg.payload)
        # print("Received", data)
        self.make_plot(data)

    async def run_loop(self):
        print("Making connection")
        client = self.connect()
        print("Starting loop")
        while True:
            client.loop()
            await asyncio.sleep(0)


app = quart.Quart(__name__)
plotter = DistancePlotter()

def frame_generator():
    while True:
        yield (
            b"--frame\r\n"
            b"Content-Type: image/png\r\n\r\n" + plotter.frame + b"\r\n"
        )

@app.route("/display")
def app_display():
    return quart.Response(frame_generator(), mimetype="multipart/x-mixed-replace; boundary=frame")

async def before_serving():
    print("Starting plotter")
    asyncio.create_task(plotter.run_loop())

# Start it all up
# asyncio.create_task(app.add_background_task(plotter_task))
app.before_serving(before_serving)
app.run(host="0.0.0.0", port=5000)
