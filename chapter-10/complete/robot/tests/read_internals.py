import time
from inventorhatmini import InventorHATMini, NUM_MOTORS

"""
Shows how to read the internal sensors of Inventor HAT Mini.

Press "User" to exit the program.
"""

# Constants
MOTOR_NAMES = ["A", "B"]      # Friendly names to give the encoders

# Create a new InventorHATMini
board = InventorHATMini(init_leds=False)

# Set the motors spinning so that a current can be measured
for motor in board.motors:
    motor.duty(1.0)

# Read the internal sensors until the user button is pressed
while not board.switch_pressed():

    # Read the voltage sense and print the value
    voltage = board.read_voltage()
    print("V =", round(voltage, 4), end=", ")

    # Read the current sense of each motor and print the value
    for i in range(NUM_MOTORS):
        current = board.read_motor_current(i)
        print(f"Current {MOTOR_NAMES[i]} = ", round(current, 4), end=", ")

    # Print a new line
    print()

    time.sleep(0.5)

# Disable the motors
for motor in board.motors:
    motor.disable()
