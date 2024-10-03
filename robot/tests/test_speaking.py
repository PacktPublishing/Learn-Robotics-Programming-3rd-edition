import pyttsx3
engine = pyttsx3.init()

engine.say("Hello, I am a robot.")
engine.runAndWait()
print(engine.getProperty('rate'))
engine.setProperty('rate', 150)
engine.setProperty('pitch', 30)
engine.setProperty('voice', 'english_rp')

def list_voices():
    voices = engine.getProperty('voices')
    for voice in voices:
        print(voice.id)
        print(voice.name)
        print(voice.languages)
        
def speak(text):
    engine.say(text)
    engine.runAndWait()
