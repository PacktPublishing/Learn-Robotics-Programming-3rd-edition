# Note - stop the inventor_hat_service before trying to run this
# plug the pan servo into the first slot
# DO NOT attach it yet, you may need to adjust what "mid" is.
# use update code to upload this. Although you can also do so from under the robot
# ssh in, systemctl stop inventor_hat_service
# then run this code sudo robotpy robot/tests/test_servo_motors.py
# Then swap the servo to the second slot and run again
from time import sleep
import inventorhatmini

board = inventorhatmini.InventorHATMini()
test_servo = board.servos[inventorhatmini.SERVO_2]

# Set the servo to the middle position
test_servo.to_mid()
sleep(1)
# Lets deflect a bit
test_servo.value(test_servo.mid_value() + 10)
sleep(1)

test_servo.value(test_servo.mid_value() - 30)
sleep(1)

test_servo.to_mid()
sleep(1)

test_servo.value(test_servo.mid_value() + 70)
sleep(1)
test_servo.to_mid()
sleep(1)
# The tilt servo requires you to:
# - Unbolt the servo horn from the servo
