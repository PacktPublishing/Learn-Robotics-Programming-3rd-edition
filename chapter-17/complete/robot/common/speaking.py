import numpy as np
from piper import PiperVoice
import sounddevice as sd


def check_audio_devices():
    """Raise RuntimeError if required input or output audio devices are unavailable."""
    devices = sd.query_devices()
    has_input = any(d['max_input_channels'] > 0 for d in devices)
    has_output = any(d['max_output_channels'] > 0 for d in devices)
    if not has_input:
        raise RuntimeError("No audio input device found — cannot listen for commands.")
    if not has_output:
        raise RuntimeError("No audio output device found — cannot speak responses.")


class VoiceSynthesizer:
    def __init__(self):
        self.voice = PiperVoice.load("en_US-ryan-low.onnx")
        self.stream = sd.OutputStream(
            samplerate=self.voice.config.sample_rate,
            channels=1
        )
        self.stream.start()

    def speak(self, text):
        for chunk in self.voice.synthesize(text):
            self.stream.write(chunk.audio_float_array)
        self.stream.write(
            np.zeros((int(0.02 * self.stream.samplerate), 1), dtype=np.float32)
        )

