import json

import sounddevice as sd
from vosk import Model, KaldiRecognizer

sample_rate = 44100

wake_word = "robot"
unknown = "[unk]"

utterances = [
    "start tracking faces",
    "track faces",
    "start following lines",
    "follow lines",
    "start tracking objects",
    "track objects",
    "start object tracking",
    "start face tracking",
    "stop",
]

full_vocabulary = utterances + [wake_word, unknown]

recognizer = KaldiRecognizer(Model(lang="en-us"), sample_rate, json.dumps(full_vocabulary))

# Transcribe until stopped
with sd.InputStream(samplerate=sample_rate, channels=1, dtype="int16") as stream:
    while True:
        audio_data = stream.read(int(0.2 * sample_rate))
        if recognizer.AcceptWaveform(audio_data[0].tobytes()):
            result = json.loads(recognizer.Result())
            text = result.get('text', '')
            if text.startswith(wake_word) and unknown not in text:
                print("Recognized:", text)
        else:
            result = json.loads(recognizer.PartialResult())
            partial = result.get('partial', '')
            if partial.startswith(wake_word):
                print("Partial:", partial)

