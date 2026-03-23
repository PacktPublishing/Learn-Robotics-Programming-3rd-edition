import numpy as np
from piper import PiperVoice
import sounddevice as sd

voice = PiperVoice.load("en_US-ryan-low.onnx")

stream = sd.OutputStream(samplerate=voice.config.sample_rate,
                   channels=1)

stream.start()

def speak(text):
    for chunk in voice.synthesize(text):
        data = chunk.audio_float_array
        stream.write(data)
    stream.write(np.zeros((int(0.02 * stream.samplerate), 1),
                          dtype=np.float32))

