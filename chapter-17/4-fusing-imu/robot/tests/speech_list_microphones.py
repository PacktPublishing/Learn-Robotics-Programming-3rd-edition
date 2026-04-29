import speech_recognition as sr

print(list(enumerate(sr.Microphone.list_microphone_names())))
