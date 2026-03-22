import json

from piper import PiperVoice
import pyaudio
import speech_recognition as sr

CHANNELS = 1
RATE = 16000

print("Loading voice...")
voice = PiperVoice.load("/home/danny/en_GB-alan-low.onnx")


def speak(text):
    raw_audio = voice.synthesize_stream_raw(text)
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=CHANNELS, rate=RATE, output=True)
    for frame in raw_audio:
        stream.write(frame)
    stream.stop_stream()
    stream.close()
    p.terminate()

rec = sr.Recognizer()
mic = sr.Microphone(device_index=4)

try:
    speak("A moment of silence, please...")
    with mic as source:
        assert source is not None
        rec.adjust_for_ambient_noise(source)
    print("Set minimum energy threshold to {}".format(rec.energy_threshold))
    while True:
        speak("Say something!")
        with mic as source:
            audio = rec.listen(source)
        speak("Got it! Now to recognize it...")
        try:
            value = rec.recognize_vosk(audio)
            text = json.loads(value)["text"]
            speak("You said {}".format(text))
            if text == "exit":
                speak("Goodbye!")
                break
        except sr.UnknownValueError:
            speak("Oops! Didn't catch that")
        except sr.RequestError as e:
            print("Uh oh! Couldn't request results from Vosk; {0}".format(e))
except KeyboardInterrupt:
    pass
