# hospital_voice_chat.py

from gpt4all import GPT4All
import pyttsx3
import random
import json
import os
import queue
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import re

# -------------------------------
# 1️⃣ Base prompts & responses
# -------------------------------

base_prompts = {
    "accident_fracture": ["I broke my leg", "I think my bone is fractured"],
    "malaria_fever": ["I have malaria symptoms", "I have high fever and chills"],
    "typhoid_infection": ["I have stomach pain and fever", "I feel weak for weeks now"],
    "pregnancy": ["I have bleeding in pregnancy", "My baby is not moving"],
}

safe_responses = {
    "accident_fracture": "This sounds serious. Avoid movement and visit the hospital. You can try elevating the injured limb to reduce pain.",
    "malaria_fever": "Check your temperature and visit the hospital. Drink fluids and rest while waiting.",
    "typhoid_infection": "Consult a doctor. Drink water and eat light meals to manage symptoms.",
    "pregnancy": "Contact your healthcare provider immediately. Try to stay calm and rest while seeking help.",
}

high_risk = ["accident_fracture", "pregnancy"]
medium_risk = ["malaria_fever", "typhoid_infection"]

# -------------------------------
# 2️⃣ Load GPT4All model
# -------------------------------

model = GPT4All("mistral-7b-openorca.gguf2.Q4_0.gguf", model_path="./models")

# -------------------------------
# 3️⃣ Helper functions
# -------------------------------

def clean_lines(text):
    lines = []
    for line in text.split("\n"):
        line = re.sub(r"^[\-\d\.\•\s]+", "", line).strip()
        if len(line) > 5:
            lines.append(line)
    return list(set(lines))

# -------------------------------
# 4️⃣ Setup TTS
# -------------------------------

engine = pyttsx3.init()
engine.setProperty('rate', 150)  # speech rate

def speak(text):
    engine.say(text)
    engine.runAndWait()

# -------------------------------
# 5️⃣ Setup Vosk (offline STT)
# -------------------------------

model_path = "models/vosk/vosk-model-small-en-us-0.15"
if not os.path.exists(model_path):
    print("Download Vosk model first!")
    exit(1)

vosk_model = Model(model_path)
q = queue.Queue()

def callback(indata, frames, time, status):
    if status:
        print(status)
    q.put(bytes(indata))

def listen_vosk(duration=5):
    rec = KaldiRecognizer(vosk_model, 16000)
    result_text = ""
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=callback):
        print("🎤 Listening...")
        for _ in range(int(duration * 1000 / 30)):
            data = q.get()
            if rec.AcceptWaveform(data):
                res = json.loads(rec.Result())
                result_text += res.get("text", "") + " "
        res = json.loads(rec.FinalResult())
        result_text += res.get("text", "")
    return result_text.strip()

# -------------------------------
# 6️⃣ Chat loop
# -------------------------------

print("🤖 Hospital AI Nurse is ready. Say something or type 'exit' to quit.")

while True:
    choice = input("Type 'speak' to talk or enter text: ").strip().lower()

    if choice == "exit":
        print("Goodbye!")
        break

    if choice == "speak":
        user_input = listen_vosk()
        print("You said:", user_input)
    else:
        user_input = choice

    # -------------------------------
    # 7️⃣ Generate GPT4All response
    # -------------------------------

    gen_prompt = f"""
You are a sympathetic Nigerian nurse. Respond to the patient:
"{user_input}"
Include emotional support and suggest ways to relieve pain or manage the situation before visiting the hospital.
"""
    try:
        response = model.generate(gen_prompt, max_tokens=300)
    except Exception as e:
        response = "Sorry, I could not process that. Please try again."
        print("Error:", e)

    print("\n", response)
    speak(response)
