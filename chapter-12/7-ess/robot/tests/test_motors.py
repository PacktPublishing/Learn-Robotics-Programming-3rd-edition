from time import sleep
import atexit
import inventorhatmini

board = inventorhatmini.InventorHATMini()
left_motor = board.motors[1]
right_motor = board.motors[0]


def stop_motors():
    left_motor.stop()
    right_motor.stop()
atexit.register(stop_motors)

left_motor.enable()
left_motor.speed(0.8)
right_motor.enable()
right_motor.speed(0.8)
sleep(2)
