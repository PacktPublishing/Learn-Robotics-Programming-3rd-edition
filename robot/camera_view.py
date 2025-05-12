from common.image_app_core import start
import cv2

def processor(frame):

    middle = (frame.shape[1] // 2, frame.shape[0] // 2)
    green = (0, 255, 0)
    # Draw a cross hair in the middle of the frame
    cv2.line(frame,
             (middle[0] - 10, middle[1]),
             (middle[0] + 10, middle[1]),
             green, 2)
    cv2.line(frame,
            (middle[0], middle[1] - 10),
            (middle[0], middle[1] + 10),
            green, 2)

    return frame

if __name__ == "__main__":
    start(processor)
