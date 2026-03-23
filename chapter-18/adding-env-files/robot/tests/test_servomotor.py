from time import sleep
import atexit
import inventorhatmini

board = inventorhatmini.InventorHATMini()
servo = board.servos[0]


def stop_servo():
    servo.disable()


atexit.register(stop_servo)


# servo.enable()
# servo.value(-70)
# sleep(2)
# servo.value(0)
# sleep(2)
# servo.value(60)
# sleep(2)
start_position = -70
end_position = 60
steps = 100
total_time = 1.0
time_per_step = total_time / steps
movement_per_step = (end_position - start_position) / steps
current_position = start_position

for n in range(steps):
    servo.value(current_position)
    current_position += movement_per_step
    sleep(time_per_step)
