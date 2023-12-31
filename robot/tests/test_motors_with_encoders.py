from time import monotonic, sleep
import inventorhatmini

board = inventorhatmini.InventorHATMini(motor_gear_ratio=120)
left_motor = board.motors[1]
right_motor = board.motors[0]

left_encoder = board.encoders[1]
right_encoder = board.encoders[0]

def encoder_sleep(seconds):
    start_time = monotonic()
    while monotonic() - start_time < seconds:
        print(left_encoder.capture().degrees,
              right_encoder.capture().degrees, 
              f"{board.read_voltage()}v")
        sleep(0.1)


speed = 0.8
try:
    left_motor.enable()
    left_motor.speed(speed)
    right_motor.enable()
    right_motor.speed(speed)
    encoder_sleep(2)
    left_motor.stop()
    # encoder_sleep(0.1)
    # right_motor.enable()
    # right_motor.speed(speed)
    # encoder_sleep(2)
    # right_motor.stop()
    # encoder_sleep(0.1)
    # left_motor.enable()
    # left_motor.speed(speed)
    # encoder_sleep(2)
finally:
    left_motor.stop()
    right_motor.stop()
