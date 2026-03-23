import time

from behavior_path import BehaviorPath
from common.mqtt_behavior import connect, publish_json


class TrajectoryBehaviorBase(BehaviorPath):
    """Base class for repeatable trajectory runner services.

    Subclasses should implement ``run_trajectory`` using BehaviorPath motion
    primitives such as ``drive_line`` and ``drive_curve``.
    """

    trajectory_tag = "trajectory"
    pause_s = 0.75

    def run_trajectory(self, client):
        raise NotImplementedError()

    def pause(self):
        time.sleep(self.pause_s)

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")
        client.subscribe("sensors/encoders/data")
        client.message_callback_add("sensors/encoders/data", self.on_encoders_data)
        client.subscribe("config/updated")
        client.message_callback_add("config/updated", self.on_config_updated)
        publish_json(client, "config/get", [
            "path/proportional",
            "path/integral",
            "path/speed",
            "path/stopping_distance",
            "robot/wheel_distance",
        ])

    def start(self):
        client = connect(on_connect=self.on_connect)

        while not self.config_ready:
            time.sleep(0.1)

        publish_json(client, "trajectory/status", {
            "tag": self.trajectory_tag,
            "status": "started",
            "time": time.time(),
        })

        try:
            self.run_trajectory(client)
            publish_json(client, "trajectory/status", {
                "tag": self.trajectory_tag,
                "status": "completed",
                "time": time.time(),
            })
        finally:
            publish_json(client, "wheel_control/enabled", False)
            publish_json(client, "motors/wheels", [0, 0])
