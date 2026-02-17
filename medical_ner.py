import dateparser
from textblob import TextBlob

conversation = {
    "symptom": None,
    "symptom_time": None,
    "severity": None
}

print(" HospitalAI Assistant Ready ")

def fix_spelling(text):
    return str(TextBlob(text).correct())


while True:
    user = input("Patient: ").strip()

    if user.lower() in ["exit", "quit", "bye"]:
        print("Bot: Thank you for chatting. Please take care ❤️")
        break


    # Fix spelling first
    corrected = fix_spelling(user)


    # Detect symptoms (simple example)
    if any(word in corrected.lower() for word in ["headache", "head ache", "pain", "fever", "cough"]):
        conversation["symptom"] = corrected
        print("Bot: I’m sorry you’re feeling unwell. When did this start?")
        continue


    # Detect time
    parsed_date = dateparser.parse(corrected)

    if parsed_date:
        conversation["symptom_time"] = parsed_date
        print("Bot: Thank you. How severe is the pain from 1 to 10?")
        continue


    # Detect severity
    if corrected.isdigit() and 1 <= int(corrected) <= 10:
        conversation["severity"] = int(corrected)

        print("\n Summary:")
        print(f"- Symptom: {conversation['symptom']}")
        print(f"- Started: {conversation['symptom_time'].strftime('%B %d, %Y')}")
        print(f"- Severity: {conversation['severity']}/10")

        print("\nBot: A doctor will review this. Please seek help if it worsens 🚑")
        continue


    # Fallback (natural response)
    print("Bot: I’m listening. Please tell me more about how you feel.")



# from transformers import pipeline

# ner = pipeline(
#   "ner",
#   model="emilyalsentzer/Bio_ClinicalBERT",
#   aggregation_strategy="simple"
# )

# print("HospitalAI Medical Assistant Ready ")

# def doctor_reply(entities, text):

#     symptoms = []
#     diseases = []

#     for e in entities:
#         if e["entity_group"] == "Sign_symptom":
#             symptoms.append(e["word"])
#         elif e["entity_group"] == "Disease":
#             diseases.append(e["word"])

#     response = "I understand how you’re feeling. "

#     if diseases:
#         response += f"You mentioned {', '.join(diseases)}. "

#     if symptoms:
#         response += f"You are experiencing {', '.join(symptoms)}. "

#     response += "\n\n"

#     # Smart advice
#     if "chest pain" in text.lower():
#         response += " Chest pain can be serious. Please visit a hospital immediately.\n"

#     if "headache" in text.lower():
#         response += "Try resting, drinking water, and avoiding stress. If it continues, see a doctor.\n"

#     if "diabetes" in text.lower():
#         response += "Please monitor your blood sugar and follow your doctor’s advice.\n"

#     response += "\nCan you tell me when these symptoms started?"

#     return response


# while True:
#     text = input("\nPatient: ")

#     if text.lower() == "exit":
#         print("Bot: Take care  Stay healthy.")
#         break

#     entities = ner(text)

#     if not entities:
#         print("Bot: I’m sorry, I need more details. Please explain more.")
#         continue

#     reply = doctor_reply(entities, text)

#     print("\nBot:", reply)
