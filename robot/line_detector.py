import cv2
import numpy as np

from common.camera_core import start, camera_app_url
from common.mqtt_behavior import connect, publish_json

SIZE = (704, 364)
GREEN = (0, 255, 0)
RED = (0, 0, 255)


class LineDetector:
    def __init__(self):
        # self.row_number = 220
        # self.row_number = 200
        self.row_number = 180
        # self.row_number = 150
        self.client = connect()

    def find_using_diffs(self, resized):
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        blurred = cv2.blur(gray, (5, 5), 0)
        row = blurred[self.row_number].astype(np.int32)
        diff = np.diff(row)

        max_d = np.amax(diff)
        min_d = np.amin(diff)
        highest = np.where(diff == max_d)[0][0]
        lowest = np.where(diff == min_d)[0][0]

        cv2.line(resized, (0, self.row_number + 4), (320, self.row_number + 4), GREEN, 2)
        cv2.line(resized, (0, self.row_number - 4), (320, self.row_number - 4), GREEN, 2)

        if max_d < 5 or min_d > -5:
            return None

        middle = (highest + lowest) / 2
        return middle, None

    def find_using_contours(self, resized):
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        masked = cv2.inRange(gray, 0, 50)
        contours, _ = cv2.findContours(masked, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None

        largest = max(contours, key=cv2.contourArea)
        cv2.drawContours(resized, [largest], -1, GREEN, 2)
        moments = cv2.moments(largest)

        # Beware of thin/malformed contours
        if moments["m00"] == 0:
            return None
        # As we have used a mask, intensities are binary. In each of the moments, we'd multiply
        # an intensity by some function (we'll see those). But because it's binary, we multiply by
        # the presence of a pixel, or not.

        ## M00 - is the area of the contour (in pixels)
        ## M01 - Sum of Y coordinates
        ## M10 - Sum of X coordinates
        # Dividing the sum of X coordinates by the area (number of pixels in the contour) gives the mean X coordinate.
        # EG - the middle.
        middle = moments['m10'] / moments['m00']

        # There are a set of moments with "mu", which represent operations on coordinates relative to the middle
        #
        ## MU11 - Sum of XY coordinates
        ## MU02 - Sum of Y^2 coordinates - represents how spread out the contour is vertically
        ## MU20 - Sum of X^2 coordinates - represents how spread out the contour is horizontally

        ## We subtract the Y spread from the X spread.
        # This will result in a value that is positive if the contour is wider than it is tall,
        # and negative if it is taller than it is wide.
        # If we divide the sum of all coordinates by this, we get the slope of the contour.
        # Using atan2, we can get the angle of the contour from the slope components, theta.

        theta = 0.5 * np.arctan2(2*moments['mu11'], moments['mu20'] - moments['mu02'])

        return middle, theta

    def processor(self, frame):
        resized = cv2.resize(frame, (320, 240))
        # middle = self.find_using_diffs(resized)
        middle, theta = self.find_using_contours(resized)

        publish_json(
            self.client,
            "line_detector/position",
            {"line": middle, "angle": theta},
        )

        if middle is not None:
            cv2.line(resized, (int(middle), 0), (int(middle), 240), RED, 2)
        return resized

    def start(self):
        # Look down
        publish_json(self.client, "motors/servo/pan/position", 0)
        publish_json(self.client, "motors/servo/tilt/position", 80)

        self.client.subscribe("camera_view/url/get")
        self.client.message_callback_add("camera_view/url/get", camera_app_url)
        camera_app_url(self.client, None, None)
        start(self.processor, size=SIZE)


if __name__ == "__main__":
    detector = LineDetector()
    detector.start()
