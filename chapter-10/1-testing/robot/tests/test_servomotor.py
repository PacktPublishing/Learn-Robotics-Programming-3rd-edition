from time import sleep
import atexit
import inventorhatmini

board = inventorhatmini.InventorHATMini()
servo = board.servos[0]
left_encoder = board.encoders[1]
left_encoder.counts_per_rev(32 * 120)
right_encoder = board.encoders[0]
right_encoder.counts_per_rev(32 * 120)


def stop_servo():
    servo.disable()


atexit.register(stop_servo)


start_position = -70
end_position = 60
steps = 100
total_time = 1.0
time_per_step = total_time / steps
# time_per_step = 0.05
movement_per_step = (end_position - start_position) / steps
current_position = start_position
total_steps = 0

while True:
    for n in range(steps):
        total_steps += 1
        current_position = start_position + n * movement_per_step
        print(f"Step {n + 1}/{steps}, Total: {total_steps}, Current position: {current_position}")
        servo.value(current_position)
        left_data = left_encoder.capture()
        right_data = right_encoder.capture()
        print(f"Left encoder counts: {left_data.radians}, "
              f"Right encoder counts: {right_data.radians}")
        sleep(time_per_step)
    for n in range(steps):
        total_steps += 1
        current_position = end_position - n * movement_per_step
        print(f"Step {n + 1}/{steps}, Total: {total_steps}, Current position: {current_position}")
        servo.value(current_position)
        left_data = left_encoder.capture()
        right_data = right_encoder.capture()

        print(f"Left encoder counts: {left_data.radians}, "
              f"Right encoder counts: {right_data.radians}")
        sleep(time_per_step)
