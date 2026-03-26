from pyinfra.operations import files

files.line(
    name="Enable I2C 1 at 400Khz",
    line="[#]\?dtparam=i2c_arm=on.*",
    path="/boot/firmware/config.txt",
    present=True,
    replace="dtparam=i2c_arm=on,i2c_arm_baudrate=400000",
    _sudo=True,
)
# Implements https://learn.adafruit.com/raspberry-pi-i2c-clock-stretching-fixes/software-i2c
files.line(
    name="Enable software i2c-gpio controller for BNO055",
    line="^dtoverlay=i2c-gpio.*",
    path="/boot/firmware/config.txt",
    present=True,
    replace="dtoverlay=i2c-gpio,bus=2,i2c_gpio_sda=23,i2c_gpio_scl=24,i2c_gpio_delay_us=2",
    _sudo=True,
)
