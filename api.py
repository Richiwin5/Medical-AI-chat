from fastapi import FastAPI, Depends
from pydantic import BaseModel
import os
import re
from gpt4all import GPT4All
from database import get_db, get_user_memory, save_user_memory, save_chat, get_chat_history


# Load Model

MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "models",
    "mistral-7b-openorca.gguf2.Q4_0.gguf"
)
model = GPT4All(MODEL_PATH, allow_download=False)


# App Setup

app = FastAPI(title="Hospital AI API")

# Request Models

class ChatRequest(BaseModel):
    user_id: str
    message: str

class HistoryRequest(BaseModel):
    user_id: str
    limit: int = 20

# Helpers

def clean_output(text):
    remove_words = ["Doctor:", "Assistant:", "Respond:", "Bot:", "Advice:"]
    for w in remove_words:
        text = text.replace(w, "")
    text = re.sub(r"\n+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def emergency_check(text):
    danger = [
        "bleeding", "pregnant", "chest pain", "faint",
        "unconscious", "breathing", "seizure"
    ]
    return any(d in text.lower() for d in danger)

def update_memory(text, memory):
    symptoms = [
        "fever", "headache", "pain", "cough", "cold",
        "tired", "fatigue", "vomiting", "diarrhea",
        "bleeding", "swelling", "nausea"
    ]
    text = text.lower()
    for s in symptoms:
        if s in text and s not in memory["symptoms"]:
            memory["symptoms"].append(s)
    if "yesterday" in text:
        memory["duration"] = "since yesterday"
    elif "today" in text:
        memory["duration"] = "today"

def build_prompt(user_input, memory):
    context = ""
    if memory["symptoms"]:
        context += f"Symptoms: {', '.join(memory['symptoms'])}\n"
    if memory["duration"]:
        context += f"Duration: {memory['duration']}\n"
    return f"""
You are a calm, supportive hospital virtual assistant.
Do not repeat yourself.
Give short, human-like advice.
If serious, advise hospital visit.

{context}
Patient: {user_input}
Reply naturally in one short paragraph.
"""

def generate_reply(user_input, memory):
    prompt = build_prompt(user_input, memory)
    with model.chat_session():
        response = model.generate(
            prompt,
            max_tokens=150,
            temp=0.4
        )
    return clean_output(response)

# Chat Endpoint
@app.post("/chat")
def chat(request: ChatRequest, db=Depends(get_db)):
    user_id = request.user_id
    message = request.message

    # Load memory
    memory = get_user_memory(db, user_id)

    # Save user message
    save_chat(db, user_id, "user", message)

    # Update memory
    update_memory(message, memory)

    # Save memory
    save_user_memory(db, user_id, memory)

    # Emergency check
    if emergency_check(message):
        reply = "This may be serious. Please visit the hospital immediately."
        save_chat(db, user_id, "assistant", reply)
        return {"reply": reply}

    # AI Reply
    reply = generate_reply(message, memory)
    save_chat(db, user_id, "assistant", reply)

    return {
        "reply": reply,
        "memory": memory
    }


# Chat History Endpoint

@app.post("/chat/history")
def history(request: HistoryRequest, db=Depends(get_db)):
    chats = get_chat_history(db, request.user_id, request.limit)
    data = [{
        "role": c.role,
        "message": c.message,
        "time": c.timestamp.isoformat()
    } for c in reversed(chats)]  # oldest first
    return {
        "user_id": request.user_id,
        "count": len(data),
        "history": data
    }


# Health Check

@app.get("/")
def home():
    return {"status": "Hospital AI API is running"}




# from fastapi import FastAPI, Depends
# from pydantic import BaseModel
# import os
# import re
# from gpt4all import GPT4All

# from database import (
#     get_db,
#     get_user_memory,
#     save_user_memory,
#     save_chat,
#     get_chat_history
# )


# # =========================
# # Load Model
# # =========================

# MODEL_PATH = os.path.join(
#     os.path.dirname(__file__),
#     "models",
#     "mistral-7b-openorca.gguf2.Q4_0.gguf"
# )

# model = GPT4All(MODEL_PATH, allow_download=False)


# # =========================
# # App Setup
# # =========================

# app = FastAPI(title="Hospital AI API")


# # =========================
# # Request Models
# # =========================

# class ChatRequest(BaseModel):
#     user_id: str
#     message: str


# class HistoryRequest(BaseModel):
#     user_id: str
#     limit: int = 20


# # =========================
# # Helpers
# # =========================

# def clean_output(text):

#     remove_words = ["Doctor:", "Assistant:", "Respond:", "Bot:", "Advice:"]

#     for w in remove_words:
#         text = text.replace(w, "")

#     text = re.sub(r"\n+", " ", text)
#     text = re.sub(r"\s+", " ", text)

#     return text.strip()


# def emergency_check(text):

#     danger = [
#         "bleeding", "pregnant", "chest pain", "faint",
#         "unconscious", "breathing", "seizure"
#     ]

#     return any(d in text.lower() for d in danger)


# def update_memory(text, memory):

#     symptoms = [
#         "fever", "headache", "pain", "cough", "cold",
#         "tired", "fatigue", "vomiting", "diarrhea",
#         "bleeding", "swelling", "nausea"
#     ]

#     text = text.lower()

#     for s in symptoms:
#         if s in text and s not in memory["symptoms"]:
#             memory["symptoms"].append(s)

#     if "yesterday" in text:
#         memory["duration"] = "since yesterday"
#     elif "today" in text:
#         memory["duration"] = "today"


# def build_prompt(user_input, memory):

#     context = ""

#     if memory["symptoms"]:
#         context += f"Symptoms: {', '.join(memory['symptoms'])}\n"

#     if memory["duration"]:
#         context += f"Duration: {memory['duration']}\n"

#     return f"""
# You are a calm, supportive hospital virtual assistant.
# Do not repeat yourself.
# Give short, human-like advice.
# If serious, advise hospital visit.

# {context}
# Patient: {user_input}
# Reply naturally in one short paragraph.
# """


# # =========================
# # Chat API
# # =========================

# @app.post("/chat")
# def chat(request: ChatRequest, db=Depends(get_db)):

#     user_id = request.user_id
#     message = request.message

#     # Load memory
#     memory = get_user_memory(db, user_id)

#     # Save user message
#     save_chat(db, user_id, "user", message)

#     # Update memory
#     update_memory(message, memory)

#     # Save memory
#     save_user_memory(db, user_id, memory)

#     # Emergency
#     if emergency_check(message):

#         reply = "This may be serious. Please visit the hospital immediately."

#         save_chat(db, user_id, "assistant", reply)

#         return {"reply": reply}


#     # AI
#     prompt = build_prompt(message, memory)

#     with model.chat_session():
#         response = model.generate(
#             prompt,
#             max_tokens=150,
#             temp=0.4
#         )

#     reply = clean_output(response)

#     # Save AI reply
#     save_chat(db, user_id, "assistant", reply)

#     return {
#         "reply": reply,
#         "memory": memory
#     }


# # =========================
# # Chat History API
# # =========================

# @app.post("/chat/history")
# def history(request: HistoryRequest, db=Depends(get_db)):

#     chats = get_chat_history(
#         db,
#         request.user_id,
#         request.limit
#     )

#     data = []

#     for c in chats:
#         data.append({
#             "role": c.role,
#             "message": c.message,
#             "time": c.timestamp
#         })

#     return {
#         "user_id": request.user_id,
#         "count": len(data),
#         "history": data
#     }


# # =========================
# # Health Check
# # =========================

# @app.get("/")
# def home():
#     return {"status": "Hospital AI API is running"}
