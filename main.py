from nlp import extract_symptoms
from rules import MedicalExpert
from experta import Fact
from llm import chat_reply, medical_explain


sessions = {}


def process_message(session, text):

    if session not in sessions:

        sessions[session] = {
            "history": [],
            "symptoms": set(),
            "pregnant": False
        }


    user = sessions[session]

    user["history"].append(text)


    # Extract symptoms
    found = extract_symptoms(text)

    for s in found:
        user["symptoms"].add(s)


    if "pregnant" in text.lower():
        user["pregnant"] = True


    # Rule engine
    engine = MedicalExpert()
    engine.reset()

    for s in user["symptoms"]:
        engine.declare(Fact(**{s: True}))

    engine.run()


    # Emergency
    if engine.result:
        return f"⚠️ {engine.result}. Please visit hospital."


    # Medical explanation
    medical = medical_explain(
        f"Patient has {', '.join(user['symptoms'])}"
    )


    # Chat reply
    context = "\n".join(user["history"][-5:])

    prompt = f"""
You are a caring doctor.

Conversation:
{context}

Medical Info:
{medical}

Reply kindly and safely.
"""

    reply = chat_reply(prompt)

    return reply
