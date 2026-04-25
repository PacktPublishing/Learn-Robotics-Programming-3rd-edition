import time


i2c_timings_sum = 0
i2c_timings_count = 0


def i2c_profile(function):
    def wrapper(*args, **kwargs):
        global i2c_timings_sum, i2c_timings_count
        start = time.monotonic()
        try:
            return function(*args, **kwargs)
        finally:
            end = time.monotonic()
            i2c_timings_sum += end - start
            i2c_timings_count += 1
    return wrapper


def summarise_i2c_timings():
    if i2c_timings_count == 0:
        print("No I2C calls made")
    else:
        mean = i2c_timings_sum / i2c_timings_count
        print(f"Average I2C timings: {mean:.4f}s over {i2c_timings_count} calls")
