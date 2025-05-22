import cv2

from common.camera_core import start, camera_app_url
from common.mqtt_behavior import connect

SIZE = (640, 480)
MIDDLE = (SIZE[0] // 2, SIZE[1] // 2)
GREEN = (0, 255, 0)
CROSS_SIZE = 10

def draw_crosshair(frame):
    cv2.line(frame,
             (MIDDLE[0] - CROSS_SIZE, MIDDLE[1]),
             (MIDDLE[0] + CROSS_SIZE, MIDDLE[1]),
             GREEN, 2)
    cv2.line(frame,
            (MIDDLE[0], MIDDLE[1] - CROSS_SIZE),
            (MIDDLE[0], MIDDLE[1] + CROSS_SIZE),
            GREEN, 2)

    return frame

if __name__ == "__main__":
    client = connect()
    client.subscribe("camera_view/url/get")
    client.message_callback_add("camera_view/url/get", camera_app_url)
    camera_app_url(client, None, None)
    start(draw_crosshair, SIZE)
