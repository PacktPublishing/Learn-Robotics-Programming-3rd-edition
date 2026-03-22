import json

import sounddevice as sd
from vosk import Model, KaldiRecognizer

sample_rate = 44100

recognizer = KaldiRecognizer(Model(lang="en-us"), sample_rate)

with sd.InputStream(samplerate=sample_rate, channels=1, dtype="int16") as stream:
    while True:
        audio_data = stream.read(int(0.2 * sample_rate))
        if recognizer.AcceptWaveform(audio_data[0].tobytes()):
            result = json.loads(recognizer.Result())
            if result.get("text"):
                print("Recognized:", result['text'])
        else:
            result = json.loads(recognizer.PartialResult())
            if result.get('partial', ''):
                print("Partial:", result['partial'])
