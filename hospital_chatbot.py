import os
import re
from gpt4all import GPT4All

from database import (
    SessionLocal,
    get_user_memory,
    save_user_memory,
    save_chat
)

# =========================
# Load Model (ONLY ONCE)
# =========================

MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "models",
    "mistral-7b-openorca.gguf2.Q4_0.gguf"
)

model = GPT4All(MODEL_PATH, allow_download=False)


# =========================
# Clean AI Output
# =========================

def clean_output(text):
    remove_words = ["Doctor:", "Assistant:", "Respond:", "Bot:", "Advice:"]
    for w in remove_words:
        text = text.replace(w, "")

    text = re.sub(r"\n+", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r'(Remember.*?provider\.)', '', text, flags=re.I)

    return text.strip()


# =========================
# Emergency Check
# =========================

def emergency_check(text):

    danger = [
        "bleeding", "pregnant", "chest pain", "faint",
        "unconscious", "breathing", "seizure"
    ]

    for d in danger:
        if d in text.lower():
            return True

    return False

def is_recovered(text):
    
    good_phrases = [
        "i am fine",
        "i'm fine",
        "i am okay",
        "i'm okay",
        "i feel better",
        "i am well",
        "i'm well",
        "i have recovered",
        "no more pain",
        "no more fever"
    ]

    text = text.lower()

    return any(p in text for p in good_phrases)

# =========================
# Memory Update
# =========================

def update_memory(text, memory):
    
    text = text.lower()

    # Clear memory if recovered
    if is_recovered(text):

        memory["symptoms"].clear()
        memory["duration"] = None
        memory["severity"] = None

        return


    symptoms_list = [
        "fever", "headache", "pain", "cough", "cold",
        "tired", "fatigue", "vomiting", "diarrhea",
        "bleeding", "swelling", "nausea"
    ]

    for s in symptoms_list:
        if s in text and s not in memory["symptoms"]:
            memory["symptoms"].append(s)

    if "yesterday" in text:
        memory["duration"] = "since yesterday"
    elif "today" in text:
        memory["duration"] = "today"


# =========================
# Prompt Builder
# =========================

def build_prompt(user_input, memory):

    context = ""

    if memory["symptoms"]:
        context += f"Symptoms: {', '.join(memory['symptoms'])}\n"

    if memory["duration"]:
        context += f"Duration: {memory['duration']}\n"

    prompt = f"""
You are a calm, supportive hospital virtual assistant.
Do not repeat yourself.
Give short, human-like advice.
If serious, advise hospital visit.

{context}
Patient: {user_input}
Reply naturally in one short paragraph.
"""

    return prompt


# =========================
# Main Chat (Terminal Test)
# =========================

def chat():

    print("\n🏥 Hospital Assistant Ready")
    print("Type 'exit' to quit\n")

    # Simulate logged-in user
    user_id = input("Enter your User ID: ").strip()

    if not user_id:
        print(" User ID required.")
        return

    db = SessionLocal()

    try:

        while True:

            user = input("You: ").strip()

            if not user:
                continue

            if user.lower() == "exit":
                print("Bot: Take care! Get well soon ❤️")
                break

            # Load memory
            memory = get_user_memory(db, user_id)

            # Save user chat
            save_chat(db, user_id, "user", user)

            # Update memory
            update_memory(user, memory)

            # Save memory
            save_user_memory(db, user_id, memory)

            # Emergency
            if emergency_check(user):

                reply = (
                    "This may be serious. "
                    "Please visit the hospital immediately."
                )

                print("\nBot:", reply, "\n")

                save_chat(db, user_id, "assistant", reply)

                continue

            # AI Response
            prompt = build_prompt(user, memory)

            with model.chat_session():
                response = model.generate(
                    prompt,
                    max_tokens=150,
                    temp=0.4
                )

            reply = clean_output(response)

            print("\nBot:", reply, "\n")

            # Save AI reply
            save_chat(db, user_id, "assistant", reply)

    finally:
        db.close()


# =========================
# Run
# =========================

# if __name__ == "__main__":
#     chat()



# from gpt4all import GPT4All
# import re


# # =========================
# # Load Model (ONLY ONCE)
# # =========================

# model = GPT4All("mistral-7b-instruct-v0.1.Q4_0.gguf")


# # =========================
# # Start ONE Chat Session
# # =========================

# session = model.chat_session()
# session.__enter__()


# # =========================
# # Conversation Memory
# # =========================

# memory = {
#     "symptoms": [],
#     "duration": None,
#     "severity": None
# }


# # =========================
# # Clean AI Output
# # =========================

# def clean_output(text):

#     remove_words = [
#         "Doctor:",
#         "Assistant:",
#         "Respond:",
#         "Bot:",
#         "Advice:"
#     ]

#     for w in remove_words:
#         text = text.replace(w, "")

#     text = re.sub(r"\n+", "\n", text)

#     return text.strip()


# # =========================
# # Emergency Check
# # =========================

# def emergency_check(text):

#     danger = [
#         "bleeding",
#         "pregnant",
#         "chest pain",
#         "faint",
#         "unconscious",
#         "breathing",
#         "seizure"
#     ]

#     for d in danger:
#         if d in text.lower():
#             return True

#     return False


# # =========================
# # Prompt Builder
# # =========================

# def build_prompt(user_input):

#     context = ""

#     if memory["symptoms"]:
#         context += f"Symptoms: {', '.join(memory['symptoms'])}\n"

#     if memory["duration"]:
#         context += f"Duration: {memory['duration']}\n"


#     prompt = f"""
# You are a hospital virtual assistant.

# Rules:
# - Be calm
# - Be human
# - Be supportive
# - Be natural
# - Do not repeat greetings
# - Do not change roles
# - Give simple advice
# - If serious, advise hospital visit

# {context}

# Patient: {user_input}

# Reply naturally:
# """

#     return prompt


# # =========================
# # Save Memory
# # =========================

# def update_memory(text):

#     symptoms_list = [
#         "fever", "headache", "pain", "cough", "cold",
#         "tired", "fatigue", "vomiting", "diarrhea",
#         "bleeding", "swelling", "nausea"
#     ]

#     for s in symptoms_list:
#         if s in text.lower() and s not in memory["symptoms"]:
#             memory["symptoms"].append(s)

#     if "yesterday" in text.lower():
#         memory["duration"] = "since yesterday"

#     if "today" in text.lower():
#         memory["duration"] = "today"

#     if "week" in text.lower():
#         memory["duration"] = "for some days"


# # =========================
# # Main Chat Loop
# # =========================

# def chat():

#     print("\n🏥 Hospital Assistant Ready ✅")
#     print("Type 'exit' to quit\n")


#     while True:

#         user = input("You: ").strip()


#         # Exit
#         if user.lower() == "exit":

#             session.__exit__(None, None, None)

#             print("\nBot: Take care. Get well soon ❤️\n")
#             break


#         if not user:
#             continue


#         # Save memory
#         update_memory(user)


#         # Emergency check
#         if emergency_check(user):

#             print("\n🚨 Bot: This may be serious.")
#             print("Please visit the nearest hospital immediately.\n")
#             continue


#         # Build prompt
#         prompt = build_prompt(user)


#         # Generate response (ONCE)
#         response = model.generate(
#             prompt,
#             max_tokens=250,
#             temp=0.4
#         )


#         # Clean output
#         response = clean_output(response)


#         print("\nBot:", response, "\n")


# # =========================
# # Run
# # =========================

# if __name__ == "__main__":
#     chat()





# from gpt4all import GPT4All
# import json
# import difflib
# import random
# import re

# # -------------------------------
# # Load Model
# # -------------------------------
# model = GPT4All(
#     "mistral-7b-openorca.gguf2.Q4_0.gguf",
#     model_path="./models"
# )

# # -------------------------------
# # Load Dataset (optional QA prompts)
# # -------------------------------
# DATA_FILE = "hospital_full_merged.jsonl"
# dataset = []
# with open(DATA_FILE, "r", encoding="utf-8") as f:
#     for line in f:
#         dataset.append(json.loads(line))

# # -------------------------------
# # Greetings / Empathy
# # -------------------------------
# GREETINGS = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
# EMPATHY_STARTERS = [
#     "I’m sorry you’re feeling this way.",
#     "That sounds uncomfortable.",
#     "I understand your concern.",
#     "Thank you for telling me.",
#     "I’m glad you reached out.",
#     "I’m here to support you."
# ]

# def is_greeting(text):
#     return any(g in text.lower() for g in GREETINGS)

# def is_how_are_you(text):
#     return "how are you" in text.lower()

# def add_empathy(text):
#     return f"{random.choice(EMPATHY_STARTERS)} {text}"

# # -------------------------------
# # Medical Knowledge Base
# # -------------------------------
# MEDICAL_KB = {
#     "malaria": "Malaria can cause fever, headache, vomiting, and weakness. Please visit a hospital for testing.",
#     "typhoid": "Typhoid often causes stomach pain and long fever. A doctor should run tests.",
#     "covid": "COVID-19 may cause cough, fever, and weakness. Rest and seek care if severe.",
#     "hepatitis": "Hepatitis affects the liver. Blood tests are needed.",
#     "diabetes": "Diabetes affects blood sugar. Diet and medication are important.",
#     "asthma": "Asthma affects breathing. Use inhalers and avoid triggers.",
#     "pregnancy": "Pregnancy requires good nutrition, rest, and regular hospital visits.",
#     "preeclampsia": "High blood pressure in pregnancy is dangerous. Please go to hospital immediately.",
#     "ulcer": "Ulcers cause stomach pain. Avoid spicy food and stay hydrated.",
#     "depression": "Depression affects mood and energy. You are not alone. Consider counseling.",
#     "stroke": "Stroke is an emergency. Go to hospital immediately.",
#     "heart attack": "Chest pain and weakness is an emergency. Call emergency services immediately."
# }

# # -------------------------------
# # Helper Functions
# # -------------------------------
# def find_best_match(user_text):
#     user_text = user_text.lower()
#     prompts = [row["prompt"].lower() for row in dataset]
#     matches = difflib.get_close_matches(user_text, prompts, n=1, cutoff=0.65)
#     if matches:
#         for row in dataset:
#             if row["prompt"].lower() == matches[0]:
#                 return row
#     return None

# def clean_reply(text):
#     bad_phrases = ["for example", "classification", "category", "severity"]
#     for p in bad_phrases:
#         if p in text.lower():
#             return "Please tell me more so I can help you better."
#     return text.strip()

# # -------------------------------
# # Conversation State
# # -------------------------------
# conversation_state = {
#     "history": [],
#     "symptoms": set(),
#     "is_pregnant": False,
#     "follow_up": None
# }

# # -------------------------------
# # Main Chat Loop
# # -------------------------------
# print("\n🏥 Hospital Assistant Ready ✅")
# print("Type 'exit' to quit\n")

# while True:
#     user_input = input("You: ").strip()
#     if user_input.lower() == "exit":
#         print("\nBot: Take care of yourself ❤️ Stay healthy.\n")
#         break

#     conversation_state["history"].append(f"Patient: {user_input}")
#     user_text = user_input.lower()

#     # -------------------
#     # Emergency Detection
#     # -------------------
#     if any(x in user_text for x in ["chest pain", "stroke", "severe bleeding", "heart attack", "collapse"]):
#         print("\nBot: ⚠️ This is an emergency. Please go to the nearest hospital immediately!\n")
#         continue

#     # -------------------
#     # Track Symptoms
#     # -------------------
#     if "headache" in user_text:
#         conversation_state["symptoms"].add("headache")
#     if "fever" in user_text or "hot" in user_text:
#         conversation_state["symptoms"].add("fever")
#     if "vomit" in user_text or "throw up" in user_text:
#         conversation_state["symptoms"].add("vomiting")
#     if "swollen" in user_text or "pain in leg" in user_text:
#         conversation_state["symptoms"].add("swelling")
#     if "tired" in user_text or "weak" in user_text:
#         conversation_state["symptoms"].add("fatigue")
#     if "pregnant" in user_text:
#         conversation_state["is_pregnant"] = True
#         conversation_state["symptoms"].add("pregnancy")

#     # -------------------
#     # Knowledge Base Check
#     # -------------------
#     kb_triggered = False
#     for illness, info in MEDICAL_KB.items():
#         if illness in user_text:
#             response = add_empathy(info)
#             print("\nBot:", response, "\n")
#             kb_triggered = True
#             if illness == "pregnancy":
#                 conversation_state["follow_up"] = "pregnancy"
#             elif illness in ["malaria", "typhoid"]:
#                 conversation_state["follow_up"] = "fever_duration"
#             break
#     if kb_triggered:
#         continue

#     # -------------------
#     # Smart Diagnosis (Multiple Symptoms)
#     # -------------------
#     if {"fever", "headache", "vomiting"}.issubset(conversation_state["symptoms"]):
#         response = add_empathy(
#             "You have fever, headache, and vomiting. This could be malaria, infection, or dehydration."
#         )
#         print("\nBot:", response)
#         if conversation_state["is_pregnant"]:
#             print("Bot: Since you are pregnant, please visit a hospital as soon as possible.\n")
#         else:
#             print("Bot: Please go for medical tests if this continues.\n")
#         continue

#     # -------------------
#     # Follow-up Handling
#     # -------------------
#     if conversation_state["follow_up"] == "pregnancy":
#         print("\nBot: How many weeks pregnant are you, and have you visited a hospital yet?\n")
#         conversation_state["follow_up"] = None
#         continue
#     if conversation_state["follow_up"] == "fever_duration":
#         print("\nBot: How many days have you had this fever?\n")
#         conversation_state["follow_up"] = None
#         continue

#     # -------------------
#     # Greetings
#     # -------------------
#     if is_how_are_you(user_input):
#         print("\nBot: I’m doing well. How are you feeling today?\n")
#         continue
#     if is_greeting(user_input):
#         print("\nBot: Hello! How can I help you today?\n")
#         continue

#     # -------------------
#     # Dataset Matching
#     # -------------------
#     match = find_best_match(user_input)
#     if match:
#         response = add_empathy(match["response"])
#         print("\nBot:", response, "\n")
#         continue

#     # -------------------
#     # AI Fallback (Memory-Aware, Friendly)
#     # -------------------
#     context = "\n".join(conversation_state["history"][-5:])
#     prompt = f"""
# You are a caring hospital assistant chatting naturally with a patient.

# Conversation so far:
# {context}

# Patient: {user_input}

# Respond empathetically, ask gentle follow-up questions if needed,
# suggest safe home care (foods, rest, mild OTC meds) if appropriate,
# and instruct urgent hospital visits if necessary.
# Keep answers concise, friendly, and human-like.
# Do NOT start your response with "Doctor:" or "Patient:".
# """
#     reply = model.generate(prompt, max_tokens=250)
#     reply = clean_reply(reply)
#     reply = add_empathy(reply)
#     reply = re.sub(r"^(Doctor:|Patient:)\s*", "", reply, flags=re.IGNORECASE)
#     print("\nBot:", reply, "\n")
