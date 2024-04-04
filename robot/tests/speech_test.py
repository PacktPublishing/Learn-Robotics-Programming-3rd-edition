import speech_recognition as sr
import json

ec = sr.Recognizer()
mic = sr.Microphone(device_index=4)

try:
    print("A moment of silence, please...")
    with mic as source:
        assert source is not None
        rec.adjust_for_ambient_noise(source)
    print("Set minimum energy threshold to {}".format(rec.energy_threshold))
    while True:
        print("Say something!")
        with mic as source:
            audio = rec.listen(source)
        print("Got it! Now to recognize it...")
        try:
            value = rec.recognize_vosk(audio)
            text = json.loads(value)["text"]
            print("You said {}".format(text))
            if text == "exit":
                print("Goodbye!")
                break
        except sr.UnknownValueError:
            print("Oops! Didn't catch that")
        except sr.RequestError as e:
            print("Uh oh! Couldn't request results from Vosk; {0}".format(e))
except KeyboardInterrupt:
    pass
