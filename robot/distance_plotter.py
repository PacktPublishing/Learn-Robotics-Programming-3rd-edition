import quart
import asyncio
import ujson as json
import io
import numpy as np
from matplotlib.figure import Figure
from mqtt_behavior import connect

class DistancePlotter:
    def __init__(self) -> None:
        self.sensor_data = np.zeros((8, 8))

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")
        client.subscribe("sensors/distance_mm")
        client.message_callback_add("sensors/distance_mm", self.data_received)

    def data_received(self, client, userdata, msg):
        self.sensor_data = json.loads(msg.payload)

    def make_plot(self):
        as_array = np.array(self.sensor_data)
        as_array = np.log(as_array)
        fig = Figure()
        ax = fig.subplots()
        ax.imshow(as_array, cmap="Greys_r")
        img = io.BytesIO()
        fig.savefig(img, format="png", dpi=80)
        return img.getbuffer()

    async def run_loop(self):
        client = connect(on_connect=self.on_connect, start_loop=False)
        print("Starting loop")
        while True:
            client.loop()
            await asyncio.sleep(0)


app = quart.Quart(__name__)
plotter = DistancePlotter()

async def frame_generator():
    while True:
        yield (
            b"--frame\r\n"
            b"Content-Type: image/png\r\n\r\n" + plotter.make_plot() + b"\r\n"
        )
        await asyncio.sleep(1/10)


@app.route("/display")
async def app_display():
    response = await quart.make_response(
        frame_generator(),
        200,
        {"Content-Type": "multipart/x-mixed-replace; boundary=frame"}
    )
    response.timeout = None
    return response

async def before_serving():
    print("Starting plotter")
    asyncio.create_task(plotter.run_loop())

# Start it all up
app.before_serving(before_serving)
app.run(host="0.0.0.0", port=5000)
