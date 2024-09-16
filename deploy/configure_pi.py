from pyinfra.operations import server

# Configure I2C
server.shell("raspi-config nonint do_i2c 0", _sudo=True) # Option 0 - enabled
