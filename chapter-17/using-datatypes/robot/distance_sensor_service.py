import atexit
import logging
import time

import vl53l5cx_ctypes
from common.mqtt_behavior import connect, publish_json

logger = logging.getLogger(__name__)

VALID_STATUSES = (vl53l5cx_ctypes.STATUS_RANGE_VALID,
                  vl53l5cx_ctypes.STATUS_RANGE_VALID_LARGE_PULSE)


class DistanceSensorService:
    def __init__(self):
        self.sensor = vl53l5cx_ctypes.VL53L5CX()
        self.sensor.set_resolution(8 * 8)
        self.sensor.set_ranging_frequency_hz(10)
        self.is_ranging = False

    def start_ranging(self, *args):
        logger.info("Starting ranging")
        self.sensor.start_ranging()
        self.is_ranging = True
        logger.info("Ranging started")

    def stop_ranging(self, *args):
        logger.info("Stopping ranging")
        self.sensor.stop_ranging()
        self.is_ranging = False

    def update_data(self):
        data = self.sensor.get_data()
        as_list = list(data.distance_mm[0])
        # Skip low confidence data
        for n, data in enumerate(list(data.target_status[0])):
            if data not in VALID_STATUSES:
                as_list[n] = 3000  # max 3m.
        publish_json(self.client, "sensors/distance_mm", as_list)

    def loop_forever(self):
        logger.info("Making connection")
        self.client = connect()
        self.client.subscribe("sensors/distance/control/#")
        self.client.subscribe("all/stop")
        self.client.message_callback_add(
            "sensors/distance/control/start_ranging", self.start_ranging)
        self.client.message_callback_add(
            "sensors/distance/control/stop_ranging", self.stop_ranging)
        self.client.publish("sensors/distance/status", "ready")
        self.client.message_callback_add("all/stop", self.stop_ranging)
        logger.info("Starting loop")
        while True:
            if self.is_ranging and self.sensor.data_ready():
                logger.info("Updating distance data")
                self.update_data()
            time.sleep(0.01)

logging.basicConfig(level=logging.INFO, format="%(asctime)s: [%(levelname)s] %(name)s: %(message)s")
logger.info("Initialising sensor")
service = DistanceSensorService()
atexit.register(service.stop_ranging)
service.loop_forever()
