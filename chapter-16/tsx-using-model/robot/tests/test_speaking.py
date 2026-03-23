from piper import PiperVoice
import pyaudio


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

print("Speaking")
speak("Hello, I am a robot.")
speak("I can speak.")
print("Saying, Now we can start to have a conversation")
speak("Now we can start to have a conversation.")