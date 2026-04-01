import json

import sounddevice as sd
from vosk import Model, KaldiRecognizer

from common.speaking import speak
from common.mqtt_behavior import connect

sample_rate = 44100
unknown = "[unk]"
wake_word = "robot"

class VoiceAgent:
    def __init__(self):
        self.client = connect()

        self.utterances = {
            "start tracking faces": self.start_tracking_faces,
            "start face tracking": self.start_tracking_faces,
            "look at faces": self.start_tracking_faces,
            "start looking at faces": self.start_tracking_faces,
            "track faces": self.start_tracking_faces,
            "stop tracking faces": self.stop_tracking_faces,
            "stop face tracking": self.stop_tracking_faces,
            "stop looking at faces": self.stop_tracking_faces,
            "start following lines": self.start_following_lines,
            "follow lines": self.start_following_lines,
            "stop following lines": self.stop_following_lines,
            "start tracking objects": self.start_tracking_objects,
            "track objects": self.start_tracking_objects,
            "start object tracking": self.start_tracking_objects,
            "stop tracking objects": self.stop_tracking_objects,
            "stop object tracking": self.stop_tracking_objects,
        }

        full_vocabulary = list(self.utterances.keys()) + [wake_word, unknown]
        self.recognizer = KaldiRecognizer(
            Model(lang="en-us"),
            sample_rate,
            json.dumps(full_vocabulary)
        )

    def start(self):
        speak("Robot ready for commands.")
        with sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16') as stream:
            while True:
                audio_data = stream.read(int(0.2 * sample_rate))
                command = self.recognize_audio(audio_data)
                if command:
                    self.handle_command(command)

    def recognize_audio(self, audio_data):
        if self.recognizer.AcceptWaveform(audio_data[0].tobytes()):
            result = json.loads(self.recognizer.Result())
            text = result.get('text', '')
            if text.startswith(wake_word) and unknown not in text:
                return text
        else:
            result = json.loads(self.recognizer.PartialResult())
            if result.get('partial', ''):
                print("Partial:", result['partial'])
        return None

    def handle_command(self, command):
        print("Handling command:", command)
        command = command.replace(f"{wake_word} ", "")
        task = self.utterances.get(command)
        if task:
            print("Running command:", command)
            task()
        else:
            speak("I didn't understand that task.")

    def start_tracking_faces(self):
        self.client.publish("launcher/start", "face_detector")
        self.client.publish("launcher/start", "look_at_face")
        speak("I'm now looking at faces!")

    def stop_tracking_faces(self):
        self.client.publish("launcher/stop", "face_detector")
        self.client.publish("launcher/stop", "look_at_face")
        speak("I'm no longer looking at faces.")

    def start_following_lines(self):
        self.client.publish("launcher/start", "line_detector")
        self.client.publish("launcher/start", "line_follower")
        speak("I'm now following lines!")

    def stop_following_lines(self):
        self.client.publish("launcher/stop", "line_follower")
        self.client.publish("launcher/stop", "line_detector")
        speak("I'm no longer following lines.")

    def start_tracking_objects(self):
        self.client.publish("launcher/start", "colored_object_detector")
        self.client.publish("launcher/start", "object_follower")
        speak("I'm now tracking objects!")

    def stop_tracking_objects(self):
        self.client.publish("launcher/stop", "colored_object_detector")
        self.client.publish("launcher/stop", "object_follower")
        speak("I'm no longer tracking objects.")

behavior = VoiceAgent()
behavior.start()
