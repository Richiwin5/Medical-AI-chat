import os
import re
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from gpt4all import GPT4All
from pathlib import Path

app = Flask(__name__)
CORS(app)  # Same as your working math solver

# =========================
# Load Model ONCE at startup (like your math solver)
# =========================

MODEL_FILENAME = "mistral-7b-openorca.gguf2.Q4_0.gguf"

# Try multiple possible paths (same pattern as your math solver)
possible_paths = [
    os.path.join(os.path.dirname(__file__), "models", MODEL_FILENAME),
    os.path.join(os.path.dirname(__file__), MODEL_FILENAME),
    "/app/models/" + MODEL_FILENAME,  # Docker path
    "./models/" + MODEL_FILENAME,
    MODEL_FILENAME  # Current directory
]

model = None
for path in possible_paths:
    if os.path.exists(path):
        print(f"✅ Found model at: {path}")
        try:
            model = GPT4All(path, allow_download=False)
            print("✅ Model loaded successfully!")
            break
        except Exception as e:
            print(f"❌ Error loading model from {path}: {e}")
            model = None

if model is None:
    print("⚠️  WARNING: Could not load model from any path!")
    print("Checked paths:")
    for path in possible_paths:
        print(f"  - {path}")

# =========================
# Simple In-Memory Storage (no database)
# =========================

# Simple dictionary storage (works like your math solver)
user_memory = {}
chat_history = {}

def get_user_memory_simple(user_id):
    """Get memory from dict, not database"""
    if user_id not in user_memory:
        user_memory[user_id] = {
            "symptoms": [],
            "duration": None,
            "severity": None
        }
    return user_memory[user_id]

def save_chat_simple(user_id, role, message):
    """Save chat to dict, not database"""
    if user_id not in chat_history:
        chat_history[user_id] = []
    chat_history[user_id].append({
        "role": role,
        "message": message,
        "timestamp": str(datetime.now())
    })
    # Keep only last 50 messages
    if len(chat_history[user_id]) > 50:
        chat_history[user_id] = chat_history[user_id][-50:]

# =========================
# Text Processing Functions
# =========================

def clean_output(text):
    remove_words = ["Doctor:", "Assistant:", "Respond:", "Bot:", "Advice:"]
    for w in remove_words:
        text = text.replace(w, "")
    text = re.sub(r"\n+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def emergency_check(text):
    danger = ["bleeding", "pregnant", "chest pain", "faint", 
              "unconscious", "breathing", "seizure"]
    text_lower = text.lower()
    for d in danger:
        if d in text_lower:
            return True
    return False

def is_recovered(text):
    good_phrases = ["i am fine", "i'm fine", "i am okay", "i'm okay", 
                    "i feel better", "i am well", "i'm well"]
    text_lower = text.lower()
    return any(p in text_lower for p in good_phrases)

def update_memory_simple(text, memory):
    """Update memory based on text"""
    text_lower = text.lower()
    
    if is_recovered(text_lower):
        memory["symptoms"].clear()
        memory["duration"] = None
        memory["severity"] = None
        return
    
    symptoms_list = ["fever", "headache", "pain", "cough", "cold",
                     "tired", "fatigue", "vomiting", "diarrhea",
                     "bleeding", "swelling", "nausea"]
    
    for s in symptoms_list:
        if s in text_lower and s not in memory["symptoms"]:
            memory["symptoms"].append(s)
    
    if "yesterday" in text_lower:
        memory["duration"] = "since yesterday"
    elif "today" in text_lower:
        memory["duration"] = "today"

def build_prompt_simple(user_input, memory):
    """Build prompt for AI"""
    context = ""
    if memory["symptoms"]:
        context += f"Symptoms: {', '.join(memory['symptoms'])}\n"
    if memory["duration"]:
        context += f"Duration: {memory['duration']}\n"
    
    prompt = f"""
You are a calm, supportive hospital virtual assistant.
Give short, human-like advice.
If serious, advise hospital visit.

{context}
Patient: {user_input}
Reply naturally in one short paragraph.
"""
    return prompt

# =========================
# API Endpoints (Same pattern as your math solver)
# =========================

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "Hospital AI Assistant is Live 🏥",
        "model_loaded": model is not None
    })

@app.route("/health", methods=["GET"])
def health():
    """Simple health check like your math solver"""
    return jsonify({
        "status": "healthy",
        "model_loaded": model is not None
    })

@app.route("/chat", methods=["POST"])
def chat():
    """Simple chat endpoint - same pattern as your /solve-text"""
    
    # Get JSON data (same as your math solver)
    data = request.get_json()
    
    if not data or "message" not in data:
        return jsonify({"error": "No message provided"}), 400
    
    # Get parameters
    user_id = data.get("user_id", "anonymous")  # Default if not provided
    user_message = data["message"]
    
    print(f"Received from {user_id}: {user_message}")
    
    # Check if model is loaded
    if model is None:
        return jsonify({
            "error": "Model not loaded",
            "reply": "I'm currently unavailable. Please try again later."
        }), 503
    
    # Check emergency first
    if emergency_check(user_message):
        reply = "This may be serious. Please visit the hospital immediately."
    else:
        try:
            # Get user memory
            memory = get_user_memory_simple(user_id)
            
            # Update memory
            update_memory_simple(user_message, memory)
            
            # Save to memory dict
            user_memory[user_id] = memory
            
            # Save chat
            save_chat_simple(user_id, "user", user_message)
            
            # Generate response
            prompt = build_prompt_simple(user_message, memory)
            
            # Use model (same pattern every time)
            with model.chat_session():
                response = model.generate(
                    prompt,
                    max_tokens=150,
                    temp=0.4
                )
            
            reply = clean_output(response)
            
            # Save reply
            save_chat_simple(user_id, "assistant", reply)
            
        except Exception as e:
            print(f"Error: {e}")
            reply = "I encountered an error. Please try again."
    
    print(f"Reply: {reply}")
    
    # Return response (same format as your math solver)
    return jsonify({
        "reply": reply,
        "user_id": user_id
    })

@app.route("/memory/<user_id>", methods=["GET"])
def get_memory(user_id):
    """Get user memory"""
    memory = get_user_memory_simple(user_id)
    return jsonify({
        "user_id": user_id,
        "memory": memory
    })

@app.route("/history/<user_id>", methods=["GET"])
def get_history(user_id):
    """Get chat history"""
    history = chat_history.get(user_id, [])
    return jsonify({
        "user_id": user_id,
        "history": history[-10:]  # Last 10 messages
    })

@app.route("/clear/<user_id>", methods=["POST"])
def clear_memory(user_id):
    """Clear user memory"""
    if user_id in user_memory:
        user_memory[user_id] = {
            "symptoms": [],
            "duration": None,
            "severity": None
        }
    return jsonify({"status": "cleared"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 6000))
    print("\n" + "="*50)
    print("🏥 Hospital AI Assistant")
    print("="*50)
    print(f"Model loaded: {'' if model else ''}")
    print(f"Port: {port}")
    print("\nTest with:")
    print(f'curl -X POST http://localhost:{port}/chat \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"user_id": "test", "message": "I have a headache"}\'')
    print("="*50)
    
    app.run(host="0.0.0.0", port=port)


# # api.py

# from flask import Flask, request, jsonify
# from flask_cors import CORS
# import os
# import re
# from gpt4all import GPT4All
# from datetime import datetime

# from database import (
#     SessionLocal,
#     get_user_memory,
#     save_user_memory,
#     save_chat,
#     get_chat_history
# )

# # =========================
# # Flask App Initialization
# # =========================

# app = Flask(__name__)
# CORS(app)  # Enable CORS for frontend applications

# # =========================
# # Load Model (ONLY ONCE)
# # =========================

# MODEL_PATH = os.path.join(
#     os.path.dirname(__file__),
#     "models",
#     "mistral-7b-openorca.gguf2.Q4_0.gguf"
# )

# # Check if model exists
# if not os.path.exists(MODEL_PATH):
#     print(f"WARNING: Model not found at {MODEL_PATH}")
#     print("Please download the model and place it in the models directory")
#     model = None
# else:
#     model = GPT4All(MODEL_PATH, allow_download=False)


# # =========================
# # Clean AI Output
# # =========================

# def clean_output(text):
#     remove_words = ["Doctor:", "Assistant:", "Respond:", "Bot:", "Advice:"]
#     for w in remove_words:
#         text = text.replace(w, "")

#     text = re.sub(r"\n+", " ", text)
#     text = re.sub(r"\s+", " ", text)
#     text = re.sub(r'(Remember.*?provider\.)', '', text, flags=re.I)

#     return text.strip()


# # =========================
# # Emergency Check
# # =========================

# def emergency_check(text):
#     danger = [
#         "bleeding", "pregnant", "chest pain", "faint",
#         "unconscious", "breathing", "seizure"
#     ]

#     for d in danger:
#         if d in text.lower():
#             return True

#     return False


# def is_recovered(text):
#     good_phrases = [
#         "i am fine",
#         "i'm fine",
#         "i am okay",
#         "i'm okay",
#         "i feel better",
#         "i am well",
#         "i'm well",
#         "i have recovered",
#         "no more pain",
#         "no more fever"
#     ]

#     text = text.lower()

#     return any(p in text for p in good_phrases)


# # =========================
# # Memory Update
# # =========================

# def update_memory(text, memory):
#     text = text.lower()

#     # Clear memory if recovered
#     if is_recovered(text):
#         memory["symptoms"].clear()
#         memory["duration"] = None
#         memory["severity"] = None
#         return

#     symptoms_list = [
#         "fever", "headache", "pain", "cough", "cold",
#         "tired", "fatigue", "vomiting", "diarrhea",
#         "bleeding", "swelling", "nausea"
#     ]

#     for s in symptoms_list:
#         if s in text and s not in memory["symptoms"]:
#             memory["symptoms"].append(s)

#     if "yesterday" in text:
#         memory["duration"] = "since yesterday"
#     elif "today" in text:
#         memory["duration"] = "today"


# # =========================
# # Prompt Builder
# # =========================

# def build_prompt(user_input, memory):
#     context = ""

#     if memory["symptoms"]:
#         context += f"Symptoms: {', '.join(memory['symptoms'])}\n"

#     if memory["duration"]:
#         context += f"Duration: {memory['duration']}\n"

#     prompt = f"""
# You are a calm, supportive hospital virtual assistant.
# Do not repeat yourself.
# Give short, human-like advice.
# If serious, advise hospital visit.

# {context}
# Patient: {user_input}
# Reply naturally in one short paragraph.
# """

#     return prompt


# # =========================
# # API Routes
# # =========================

# @app.route('/health', methods=['GET'])
# def health_check():
#     """Check if the API is running and model is loaded"""
#     return jsonify({
#         'status': 'healthy',
#         'model_loaded': model is not None,
#         'timestamp': datetime.utcnow().isoformat()
#     })


# @app.route('/chat', methods=['POST'])
# def chat():
#     """
#     Send a message to the assistant
    
#     Expected JSON payload:
#     {
#         "user_id": "user123",
#         "message": "I have a headache"
#     }
#     """
#     if model is None:
#         return jsonify({
#             'error': 'Model not loaded. Please check model file path.'
#         }), 500

#     data = request.get_json()
    
#     if not data:
#         return jsonify({'error': 'No JSON data provided'}), 400
    
#     user_id = data.get('user_id')
#     user_message = data.get('message')
    
#     if not user_id:
#         return jsonify({'error': 'user_id is required'}), 400
    
#     if not user_message:
#         return jsonify({'error': 'message is required'}), 400
    
#     # Create database session
#     db = SessionLocal()
    
#     try:
#         # Load user memory
#         memory = get_user_memory(db, user_id)
        
#         # Save user message to chat history
#         save_chat(db, user_id, "user", user_message)
        
#         # Update memory based on message
#         update_memory(user_message, memory)
        
#         # Save updated memory
#         save_user_memory(db, user_id, memory)
        
#         # Check for emergency
#         if emergency_check(user_message):
#             reply = "This may be serious. Please visit the hospital immediately."
#         else:
#             # Generate AI response
#             prompt = build_prompt(user_message, memory)
            
#             with model.chat_session():
#                 response = model.generate(
#                     prompt,
#                     max_tokens=150,
#                     temp=0.4
#                 )
            
#             reply = clean_output(response)
        
#         # Save assistant reply to chat history
#         save_chat(db, user_id, "assistant", reply)
        
#         return jsonify({
#             'user_id': user_id,
#             'reply': reply,
#             'memory': memory,
#             'timestamp': datetime.utcnow().isoformat()
#         })
    
#     except Exception as e:
#         db.rollback()
#         return jsonify({'error': str(e)}), 500
    
#     finally:
#         db.close()


# @app.route('/memory/<user_id>', methods=['GET'])
# def get_memory(user_id):
#     """Get the current memory state for a user"""
#     db = SessionLocal()
    
#     try:
#         memory = get_user_memory(db, user_id)
#         return jsonify({
#             'user_id': user_id,
#             'memory': memory
#         })
    
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500
    
#     finally:
#         db.close()


# @app.route('/memory/<user_id>', methods=['PUT'])
# def update_memory_api(user_id):
#     """
#     Manually update a user's memory
    
#     Expected JSON payload:
#     {
#         "symptoms": ["fever", "headache"],
#         "duration": "since yesterday",
#         "severity": "mild"
#     }
#     """
#     data = request.get_json()
    
#     if not data:
#         return jsonify({'error': 'No JSON data provided'}), 400
    
#     db = SessionLocal()
    
#     try:
#         # Get current memory
#         memory = get_user_memory(db, user_id)
        
#         # Update with provided data
#         if 'symptoms' in data:
#             memory['symptoms'] = data['symptoms']
#         if 'duration' in data:
#             memory['duration'] = data['duration']
#         if 'severity' in data:
#             memory['severity'] = data['severity']
        
#         # Save updated memory
#         save_user_memory(db, user_id, memory)
        
#         return jsonify({
#             'user_id': user_id,
#             'memory': memory,
#             'message': 'Memory updated successfully'
#         })
    
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500
    
#     finally:
#         db.close()


# @app.route('/history/<user_id>', methods=['GET'])
# def get_history(user_id):
#     """Get chat history for a user"""
#     limit = request.args.get('limit', default=50, type=int)
    
#     db = SessionLocal()
    
#     try:
#         history = get_chat_history(db, user_id, limit)
#         return jsonify({
#             'user_id': user_id,
#             'history': history,
#             'count': len(history)
#         })
    
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500
    
#     finally:
#         db.close()


# @app.route('/clear-memory/<user_id>', methods=['POST'])
# def clear_memory(user_id):
#     """Clear all memory for a user"""
#     db = SessionLocal()
    
#     try:
#         empty_memory = {
#             "symptoms": [],
#             "duration": None,
#             "severity": None
#         }
#         save_user_memory(db, user_id, empty_memory)
        
#         return jsonify({
#             'user_id': user_id,
#             'memory': empty_memory,
#             'message': 'Memory cleared successfully'
#         })
    
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500
    
#     finally:
#         db.close()


# # =========================
# # Error Handlers
# # =========================

# @app.errorhandler(404)
# def not_found(error):
#     return jsonify({'error': 'Resource not found'}), 404


# @app.errorhandler(500)
# def internal_error(error):
#     return jsonify({'error': 'Internal server error'}), 500


# # =========================
# # Run the App
# # =========================

# if __name__ == '__main__':
#     print("\n" + "="*50)
#     print(" Hospital Assistant API")
#     print("="*50)
    
#     if model is None:
#         print("⚠️  WARNING: Model not loaded!")
#         print(f"   Please ensure model exists at: {MODEL_PATH}")
#     else:
#         print(" Model loaded successfully")
    
#     print("\n Starting Flask server...")
#     print(" API Endpoints:")
#     print("   GET  /health              - Health check")
#     print("   POST /chat                 - Send a message")
#     print("   GET  /memory/<user_id>     - Get user memory")
#     print("   PUT  /memory/<user_id>     - Update user memory")
#     print("   GET  /history/<user_id>    - Get chat history")
#     print("   POST /clear-memory/<user_id> - Clear user memory")
#     print("\n💡 Test with: curl -X POST http://localhost:6000/chat \\")
#     print('     -H "Content-Type: application/json" \\')
#     print('     -d \'{"user_id": "test", "message": "I have a headache"}\'')
#     print("\n" + "="*50)
    
#     app.run(host='0.0.0.0', port=6000, debug=True)

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

