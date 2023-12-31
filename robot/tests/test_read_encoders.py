from time import monotonic, sleep
import inventorhatmini

board = inventorhatmini.InventorHATMini(motor_gear_ratio=120)

left_encoder = board.encoders[1]
right_encoder = board.encoders[0]

def encoder_sleep(seconds):
    start_time = monotonic()
    while monotonic() - start_time < seconds:
        print(left_encoder.capture().degrees,
              right_encoder.capture().degrees,
              f"{board.read_voltage()}v")
        sleep(0.1)

while True:
    encoder_sleep(2)

