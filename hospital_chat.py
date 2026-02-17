from gpt4all import GPT4All
import spacy
import random
import json
import re

# -------------------------------
# Load GPT4All Model
# -------------------------------
model = GPT4All(
    "mistral-7b-openorca.gguf2.Q4_0.gguf",
    model_path="./models"
)

# -------------------------------
# Load Biomedical Spacy Model
# -------------------------------
# Ensure you have downloaded a scispacy model compatible with your spaCy version
# e.g., pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.1/en_core_sci_sm-0.5.1.tar.gz
try:
    nlp = spacy.load("en_core_sci_sm")
except Exception:
    print("⚠️ Spacy biomedical model not found. Please install en_core_sci_sm")
    exit(1)

# -------------------------------
# Greetings / Empathy
# -------------------------------
GREETINGS = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
EMPATHY_STARTERS = [
    "I’m sorry you’re feeling this way.",
    "That sounds uncomfortable.",
    "I understand your concern.",
    "Thank you for telling me.",
    "I’m glad you reached out.",
    "I’m here to support you."
]

def is_greeting(text):
    return any(g in text.lower() for g in GREETINGS)

def is_how_are_you(text):
    return "how are you" in text.lower()

def add_empathy(text):
    return f"{random.choice(EMPATHY_STARTERS)} {text}"

# -------------------------------
# Emergency Symptoms
# -------------------------------
EMERGENCIES = ["chest pain", "stroke", "severe bleeding", "heart attack", "collapse"]

# -------------------------------
# Home Care Recommendations
# -------------------------------
HOME_CARE = {
    "headache": "Rest, stay hydrated, and consider acetaminophen (Tylenol) if safe.",
    "fever": "Drink fluids, rest, and monitor your temperature. Seek hospital if >38.5°C or persistent.",
    "nausea": "Eat small bland meals, stay hydrated, ginger tea may help.",
    "ulcer": "Avoid spicy/acidic foods, eat small frequent meals, and stay hydrated.",
    "back pain": "Rest, gentle stretching, and heat packs may help. Seek care if severe.",
    "fatigue": "Rest, maintain hydration, and balanced diet."
}

# -------------------------------
# Conversation Memory
# -------------------------------
conversation_history = []
patient_info = {
    "symptoms": set(),
    "pregnant": False,
    "onset_dates": {},
    "emergency_flag": False
}

# -------------------------------
# Helper Functions
# -------------------------------
def extract_entities(text):
    """Extract symptoms, diseases, pregnancy, and dates using Spacy."""
    doc = nlp(text)
    symptoms = []
    diseases = []
    dates = []
    
    for ent in doc.ents:
        if ent.label_ in ["DISEASE", "SIGN_SYMPTOM", "SYMPTOM", "CONDITION"]:
            symptoms.append(ent.text.lower())
        if ent.label_ in ["DATE", "TIME"]:
            dates.append(ent.text.lower())
    
    # Check for pregnancy manually
    pregnant = "pregnant" in text.lower()
    
    return symptoms, diseases, dates, pregnant

def generate_prompt(user_input):
    """Construct context-aware GPT prompt."""
    recent_history = "\n".join(conversation_history[-6:])
    symptoms = ", ".join(patient_info["symptoms"]) or "none"
    pregnant_status = "pregnant" if patient_info["pregnant"] else "not pregnant"
    
    home_care_suggestions = []
    for s in patient_info["symptoms"]:
        if s in HOME_CARE:
            home_care_suggestions.append(HOME_CARE[s])
    home_care_text = " ".join(home_care_suggestions) if home_care_suggestions else ""
    
    prompt = f"""
You are a caring hospital doctor. Be empathetic and context-aware.
Patient info: Symptoms: {symptoms}. Pregnant: {pregnant_status}. Onset dates: {patient_info['onset_dates']}
Patient conversation so far:
{recent_history}

Patient says: {user_input}

Provide advice with empathy. Include safe home care suggestions before hospital visit. Flag emergencies. Suggest immediate hospital visit if necessary. {home_care_text}
"""
    return prompt

# -------------------------------
# Chat Loop
# -------------------------------
print("\n🏥 HospitalAI Assistant Ready ✅")
print("Type 'exit' to quit\n")

while True:
    try:
        user_input = input("Patient: ").strip()
    except KeyboardInterrupt:
        print("\n\nBot: Take care of yourself ❤️ Stay healthy.\n")
        break

    if user_input.lower() == "exit":
        print("\nBot: Take care of yourself ❤️ Stay healthy.\n")
        break

    conversation_history.append(f"Patient: {user_input}")

    # Emergency detection
    if any(e in user_input.lower() for e in EMERGENCIES):
        print("\nBot: ⚠️ This is an emergency. Please call your hospital or seek immediate care!\n")
        patient_info["emergency_flag"] = True
        continue

    # Extract entities
    symptoms, diseases, dates, pregnant = extract_entities(user_input)
    patient_info["symptoms"].update(symptoms)
    if pregnant:
        patient_info["pregnant"] = True
    for s in symptoms:
        if dates:
            patient_info["onset_dates"][s] = dates[-1]  # last mentioned date

    # Greetings
    if is_how_are_you(user_input):
        print("\nBot: I’m doing well. How are you feeling today?\n")
        continue

    if is_greeting(user_input):
        print("\nBot: Hello! How can I help you today?\n")
        continue

    # Generate GPT4All response
    prompt = generate_prompt(user_input)
    reply = model.generate(prompt, max_tokens=250)
    reply = add_empathy(reply.strip())
    conversation_history.append(f"Bot: {reply}")

    print("\nBot:", reply, "\n")
