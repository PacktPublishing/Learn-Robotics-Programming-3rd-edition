from pyinfra.operations import files

files.line(
    name="Enable I2C 1 at 400Khz",
    line="[#]\?dtparam=i2c_arm=on.*",
    path="/boot/firmware/config.txt",
    present=True,
    replace="dtparam=i2c_arm=on,i2c_arm_baudrate=400000",
    _sudo=True,
)