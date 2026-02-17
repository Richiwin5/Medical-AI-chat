import spacy

nlp = spacy.load("en_core_web_sm")

SYMPTOMS = [
    "fever", "headache", "vomiting", "fatigue",
    "cough", "pain", "swelling", "weakness",
    "dizziness", "bleeding"
]

def extract_symptoms(text):

    found = set()

    doc = nlp(text.lower())

    for token in doc:
        if token.text in SYMPTOMS:
            found.add(token.text)

    return list(found)
