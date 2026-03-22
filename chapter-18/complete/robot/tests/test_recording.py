import sounddevice as sd
import time

# https://python-sounddevice.readthedocs.io/en/0.5.1/usage.html
# https://pypi.org/project/soundfile/#description
def test_record():
    duration = 10
    fs = 44100
    myrecording = sd.rec(int(duration * fs), samplerate=fs, channels=2)
    print("Speak now!")
    sd.wait()
    #
    time.sleep(1)
    print("Playing back...")
    sd.play(myrecording, samplerate=fs)
    sd.wait()


# We've proven all this works. But weaving it together...

