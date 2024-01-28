import quart
import asyncio
import ujson as json
import io
import numpy as np
from matplotlib.figure import Figure
from mqtt_behavior import connect


class DistancePlotter:
    def __init__(self) -> None:
        # self.sensor_data = np.zeros((8, 8))
        self.sensor_data = None

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")
        client.subscribe("sensors/distance_mm")
        client.message_callback_add("sensors/distance_mm", self.data_received)

    def connect(self):
        return connect(on_connect=self.on_connect, start_loop=False)

    def data_received(self, client, userdata, msg):
        try:
            raw_data = json.loads(msg.payload)
            as_array = np.array(raw_data)
            if as_array.size == 16:
                as_array = as_array.reshape((4, 4))
            else:
                as_array = as_array.reshape((8, 8))
            as_array = np.flipud(as_array)

            self.sensor_data = np.clip(as_array, 0, 300)
        except Exception as err:
            print("Error:", err)
            print("Payload:", msg.payload)

    async def make_plot(self):
        while self.sensor_data is None:
            await asyncio.sleep(0.01)
        new_data = self.sensor_data
        self.sensor_data = None

        fig = Figure()
        ax = fig.subplots()
        ax.imshow(new_data, cmap="gray")
        img = io.BytesIO()
        fig.savefig(img, format="png", dpi=80)
        return img.getbuffer()


    async def run_loop(self):
        client = self.connect()
        print("Starting loop")
        while True:
            client.loop(timeout=0.1)
            await asyncio.sleep(0.01)


app = quart.Quart(__name__)
plotter = DistancePlotter()

async def frame_generator():
    while True:
        yield (
            b"--frame\r\n"
            b"Content-Type: image/png\r\n\r\n" + await plotter.make_plot() + b"\r\n"
        )
        # await asyncio.sleep(0.1)


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
# asyncio.create_task(app.add_background_task(plotter_task))
app.before_serving(before_serving)
app.run(host="0.0.0.0", port=5000)
