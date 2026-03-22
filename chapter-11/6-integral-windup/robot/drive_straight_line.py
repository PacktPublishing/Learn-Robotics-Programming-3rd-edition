import ujson as json
import time

from bokeh.plotting import figure

# from common.bokeh_helper import start_plot, PlotData
from common.mqtt_behavior import connect, publish_json
from common.pid_controller import PIDController


class DriveStraightLineBehavior:
    def __init__(self):
        self.speed = 0.6
        self.balance_pid = PIDController(0.02)
        self.last_update = time.time()
        # self.plot_data = PlotData(["error", "balance", "time"])
        self.left_encoder_speed = 0
        self.right_encoder_speed = 0

    def on_encoders_data(self, client, userdata, message):
        encoder_data = json.loads(message.payload)
        self.left_encoder_speed = encoder_data['left_speed'] * 0.1 + self.left_encoder_speed * 0.9
        self.right_encoder_speed = encoder_data['right_speed'] * 0.1 + self.right_encoder_speed * 0.9
        new_time = time.time()
        time_difference = new_time - self.last_update
        self.last_update = new_time
        # Get the error
        error = self.left_encoder_speed - self.right_encoder_speed
        # Balance the motors
        balance = self.balance_pid.control(error, time_difference)
        print(error, time_difference, balance)
        publish_json(client, "plot/data", {"error": error, "balance": balance, "time": new_time})
        # self.plot_data.put([error, balance, time.time()])
        left_speed = self.speed - balance
        right_speed = self.speed + balance
        publish_json(client, "motors/wheels", [left_speed, right_speed])

    def start(self):
        client = connect(start_loop=False)
        client.subscribe("sensors/encoders/data")
        client.publish("sensors/encoders/control/reset")
        client.message_callback_add("sensors/encoders/data",
                                    self.on_encoders_data)
        client.loop_forever()


def setup_plot(doc, column_source):
    fig = figure(max_width=640, max_height=250)
    fig.line(source=column_source, x="time", y="error", line_color="black")
    fig.line(source=column_source, x="time", y="balance", line_color="red")
    # 0 line
    fig.ray(
        x=[0], y=[0],
        length=0, angle=0,
        line_color="green", line_dash="dashed",
    )
    doc.add_root(fig)


behavior = DriveStraightLineBehavior()
behavior.start()
# start_plot(
#     behavior.plot_data,
#     setup_plot,
# )

# Layer 2 - We want our phone app to be able to set the PID values
# Layer 3 - we are going to want to visualise this to tune the PID
