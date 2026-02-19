import os
import re
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from gpt4all import GPT4All
from database import SessionLocal, get_user_memory, save_user_memory, save_chat, get_chat_history


# Load Model ON STARTUP

print("Loading GPT4All model at startup...")

MODEL_PATH = "mistral-7b-openorca.Q4_0.gguf"  # adjust path if needed
model = None

try:
    model = GPT4All(
        MODEL_PATH,
        allow_download=True,
        device="cpu",    # enforce CPU (Render doesn’t have CUDA)
        n_threads=2
    )
    print("Model loaded successfully ")
except Exception as e:
    print(f"Failed to load GPT4All model: {e}")


# Flask App Setup

app = Flask(__name__)
CORS(app)


# Helpers

def clean_output(text):
    remove_words = ["Doctor:", "Assistant:", "Respond:", "Bot:", "Advice:"]
    for w in remove_words:
        text = text.replace(w, "")
    text = re.sub(r"\n+", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r'(Remember.*?provider\.)', '', text, flags=re.I)
    return text.strip()

def emergency_check(text):
    danger = ["bleeding", "pregnant", "chest pain", "faint", "unconscious", "breathing", "seizure"]
    return any(d in text.lower() for d in danger)

def is_recovered(text):
    good_phrases = [
        "i am fine", "i'm fine", "i am okay", "i'm okay", "i feel better",
        "i am well", "i'm well", "i have recovered", "no more pain", "no more fever"
    ]
    text = text.lower()
    return any(p in text for p in good_phrases)

def update_memory(text, memory):
    text = text.lower()
    if is_recovered(text):
        memory["symptoms"].clear()
        memory["duration"] = None
        memory["severity"] = None
        return

    symptoms_list = [
        "fever", "headache", "pain", "cough", "cold", "tired", "fatigue",
        "vomiting", "diarrhea", "bleeding", "swelling", "nausea"
    ]
    for s in symptoms_list:
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
    if memory.get("duration"):
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
        response = model.generate(prompt, max_tokens=150, temp=0.4)
    return clean_output(response)


# Routes

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Medical AI Chat API is running!",
        "routes": ["/chat (POST)", "/chat/history (POST)"]
    })

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_id = data.get("user_id")
    message = data.get("message")

    if not user_id or not message:
        return jsonify({"error": "user_id and message required"}), 400

    db = SessionLocal()
    try:
        memory = get_user_memory(db, user_id)
        save_chat(db, user_id, "user", message)
        update_memory(message, memory)
        save_user_memory(db, user_id, memory)

        if emergency_check(message):
            reply = "This may be serious. Please visit the hospital immediately."
            save_chat(db, user_id, "assistant", reply)
            return jsonify({"reply": reply})

        try:
            reply = generate_reply(message, memory)
        except Exception as e:
            return jsonify({"error": f"LLM generation failed: {str(e)}"}), 500

        save_chat(db, user_id, "assistant", reply)
        return jsonify({"reply": reply, "memory": memory})
    finally:
        db.close()

@app.route("/chat/history", methods=["POST"])
def history():
    data = request.get_json()
    user_id = data.get("user_id")
    limit = data.get("limit", 20)

    if not user_id:
        return jsonify({"error": "user_id required"}), 400

    db = SessionLocal()
    try:
        chats = get_chat_history(db, user_id, limit)
        history_data = [{
            "role": c.role,
            "message": c.message,
            "time": getattr(c, "timestamp", None).isoformat() if getattr(c, "timestamp", None) else None
        } for c in reversed(chats)]
        return jsonify({"user_id": user_id, "count": len(history_data), "history": history_data})
    finally:
        db.close()


# Run App

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)



# import os
# import re
# from flask import Flask, request, jsonify
# from flask_cors import CORS
# from gpt4all import GPT4All
# from database import SessionLocal, get_user_memory, save_user_memory, save_chat, get_chat_history

# # =========================
# # Load Model (only once)
# # =========================
# model = None  

# def get_model():
#     global model

#     if model is None:
#         print("Loading GPT4All model...")

#         model = GPT4All(
#             "mistral-7b-openorca.Q4_0.gguf",
#             allow_download=True,
#             device="cpu",
#             n_threads=2
#         )

#     return model

# # =========================
# # Flask App Setup
# # =========================
# app = Flask(__name__)
# CORS(app)

# # =========================
# # Helpers
# # =========================
# def clean_output(text):
#     remove_words = ["Doctor:", "Assistant:", "Respond:", "Bot:", "Advice:"]
#     for w in remove_words:
#         text = text.replace(w, "")
#     text = re.sub(r"\n+", " ", text)
#     text = re.sub(r"\s+", " ", text)
#     text = re.sub(r'(Remember.*?provider\.)', '', text, flags=re.I)
#     return text.strip()

# def emergency_check(text):
#     danger = ["bleeding", "pregnant", "chest pain", "faint", "unconscious", "breathing", "seizure"]
#     return any(d in text.lower() for d in danger)

# def is_recovered(text):
#     good_phrases = [
#         "i am fine", "i'm fine", "i am okay", "i'm okay", "i feel better",
#         "i am well", "i'm well", "i have recovered", "no more pain", "no more fever"
#     ]
#     text = text.lower()
#     return any(p in text for p in good_phrases)

# def update_memory(text, memory):
#     text = text.lower()
#     if is_recovered(text):
#         memory["symptoms"].clear()
#         memory["duration"] = None
#         memory["severity"] = None
#         return

#     symptoms_list = ["fever", "headache", "pain", "cough", "cold", "tired", "fatigue",
#                      "vomiting", "diarrhea", "bleeding", "swelling", "nausea"]
#     for s in symptoms_list:
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
#     if memory.get("duration"):
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

# def generate_reply(user_input, memory):
#     llm = get_model()  

#     prompt = build_prompt(user_input, memory)

#     with llm.chat_session():
#         response = llm.generate(prompt, max_tokens=150, temp=0.4)

#     return clean_output(response)


# # =========================
# # Routes
# # =========================
# @app.route("/", methods=["GET"])
# def home():
#     return jsonify({
#         "message": "Medical AI Chat API is running!",
#         "routes": ["/chat (POST)", "/chat/history (POST)"]
#     })


# @app.route("/chat", methods=["POST"])
# def chat():
#     data = request.get_json()
#     user_id = data.get("user_id")
#     message = data.get("message")

#     if not user_id or not message:
#         return jsonify({"error": "user_id and message required"}), 400

#     db = SessionLocal()
#     try:
#         memory = get_user_memory(db, user_id)
#         save_chat(db, user_id, "user", message)
#         update_memory(message, memory)
#         save_user_memory(db, user_id, memory)

#         if emergency_check(message):
#             reply = "This may be serious. Please visit the hospital immediately."
#             save_chat(db, user_id, "assistant", reply)
#             return jsonify({"reply": reply})

#         try:
#             reply = generate_reply(message, memory)
#         except Exception as e:
#             return jsonify({"error": f"LLM generation failed: {str(e)}"}), 500

#         save_chat(db, user_id, "assistant", reply)
#         return jsonify({"reply": reply, "memory": memory})
#     finally:
#         db.close()


# @app.route("/chat/history", methods=["POST"])
# def history():
#     data = request.get_json()
#     user_id = data.get("user_id")
#     limit = data.get("limit", 20)

#     if not user_id:
#         return jsonify({"error": "user_id required"}), 400

#     db = SessionLocal()
#     try:
#         chats = get_chat_history(db, user_id, limit)
#         history_data = [{
#             "role": c.role,
#             "message": c.message,
#             "time": c.timestamp.isoformat()
#         } for c in reversed(chats)]
#         return jsonify({"user_id": user_id, "count": len(history_data), "history": history_data})
#     finally:
#         db.close()


# if __name__ == "__main__":
#     port = int(os.environ.get("PORT", 8000))
#     app.run(host="0.0.0.0", port=port)

