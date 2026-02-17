# hospital_data_generator.py

from gpt4all import GPT4All
import json
import random
import re
import os

# -------------------------------
# 1️⃣ Base Categories & Prompts
# -------------------------------
base_prompts = {
    "accident_fracture": [
        "I broke my leg in an accident",
        "I fell and my arm is swollen",
        "I think my bone is fractured",
        "I slipped and injured my back",
        "My waist is hurting after falling",
        "I can’t move my leg well"
    ],
    "malaria_fever": [
        "I have malaria symptoms",
        "I have high fever and chills",
        "I’m sweating and very weak",
        "My body is hot and painful",
        "I feel cold and hot at the same time",
        "I’m shivering with fever"
    ],
    "typhoid_infection": [
        "Doctor said I may have typhoid",
        "I have stomach pain and fever",
        "I feel weak for weeks now",
        "I vomit and feel tired",
        "I can’t eat well for days",
        "My body is always tired"
    ],
    "pregnancy": [
        "I have bleeding in pregnancy",
        "My baby is not moving",
        "I have labor pain",
        "I feel dizzy while pregnant",
        "My stomach is tightening",
        "I feel sharp pain in pregnancy"
    ],
    "bleeding_wound": [
        "My wound is bleeding badly",
        "I cut myself deeply",
        "Blood is not stopping",
        "I injured my leg badly",
        "My hand is bleeding seriously",
        "I lost much blood"
    ],
    "animal_bite": [
        "A dog bit me",
        "I was bitten by a snake",
        "A cat scratched me badly",
        "A rat bit my finger",
        "A monkey scratched me",
        "A stray dog attacked me"
    ],
    "swelling_infection": [
        "My leg is swollen",
        "My face is swollen",
        "There is pus in my wound",
        "My hand is infected",
        "My toe is swollen",
        "My ear is painful and swollen"
    ],
    "respiratory": [
        "I am coughing badly",
        "I have chest pain and cough",
        "I can’t breathe well",
        "I’m short of breath",
        "My chest is tight",
        "I wheeze when breathing"
    ],
    "digestive": [
        "I have diarrhea",
        "My stomach hurts badly",
        "I vomit every day",
        "I can’t eat well",
        "I have running stomach",
        "I feel nauseous"
    ],
    "appointment": [
        "I want to see a doctor",
        "Book appointment for me",
        "I need lab test",
        "Reschedule my visit",
        "I want medical checkup",
        "I need hospital appointment"
    ]
}

# -------------------------------
# 2️⃣ Safe Responses with empathy & suggestions
# -------------------------------
safe_responses = {
    "accident_fracture": "I’m sorry you’re hurt. Please avoid moving too much. You can apply ice to reduce swelling while seeking medical attention immediately.",
    "malaria_fever": "I understand this feels awful. Make sure to rest and stay hydrated. Consider taking paracetamol while visiting the hospital for malaria testing.",
    "typhoid_infection": "I know this can be exhausting. Drink plenty of fluids, eat light meals, and consult a doctor for proper tests.",
    "pregnancy": "I’m concerned about your safety. Monitor your symptoms closely and contact your healthcare provider immediately. Rest and avoid heavy activity.",
    "bleeding_wound": "That sounds serious! Apply pressure to the wound and keep it elevated. Seek emergency medical care right away.",
    "animal_bite": "I’m sorry that happened. Wash the area with clean water and mild soap. Visit the hospital immediately for treatment and vaccines.",
    "swelling_infection": "I understand this is uncomfortable. Keep the area clean, elevate if possible, and see a doctor for proper treatment.",
    "respiratory": "Breathing issues can be scary. Try to stay calm, sit upright, and seek medical attention promptly.",
    "digestive": "I know it’s unpleasant. Stay hydrated, eat bland foods, and consult a doctor if symptoms persist.",
    "appointment": "I understand your concern. I can help you schedule an appointment at a time convenient for you."
}

# -------------------------------
# 3️⃣ Severity Rules
# -------------------------------
high_risk = ["bleeding_wound", "pregnancy", "accident_fracture", "animal_bite"]
medium_risk = ["malaria_fever", "typhoid_infection", "respiratory", "swelling_infection"]
low_risk = ["digestive", "appointment"]

# -------------------------------
# 4️⃣ Load Model
# -------------------------------
model = GPT4All(
    "mistral-7b-openorca.gguf2.Q4_0.gguf",
    model_path="./models"
)

# -------------------------------
# 5️⃣ Helper: Clean Lines
# -------------------------------
def clean_lines(text):
    lines = []
    for line in text.split("\n"):
        line = re.sub(r"^[\-\d\.\•\s]+", "", line).strip()
        if len(line) > 5:
            lines.append(line)
    return list(set(lines))

# -------------------------------
# 6️⃣ Generate Dataset
# -------------------------------
ROUNDS = 5
VARIATIONS = 10        # more variations to increase dataset
BATCH_SAVE = 1000

synthetic_data = []

for round_num in range(1, ROUNDS + 1):
    print(f"\n=== Round {round_num}/{ROUNDS} ===")
    for category, prompts in base_prompts.items():
        for base_text in prompts:
            gen_prompt = f"""
Generate {VARIATIONS} natural, empathetic ways a Nigerian patient might say:
"{base_text}"

Include emotions, sympathy, and short suggestions for relief or coping before visiting hospital.
Each on a new line.
"""

            try:
                response = model.generate(gen_prompt, max_tokens=800)
                variations = clean_lines(response)
                if not variations:
                    variations = [base_text]
            except Exception as e:
                print("Generation error:", e)
                variations = [base_text]

            for text in variations:
                severity = "high" if category in high_risk else "medium" if category in medium_risk else "low"
                intent = "emergency" if severity == "high" else ("appointment" if category=="appointment" else "complaint")

                synthetic_data.append({
                    "prompt": text,
                    "category": category,
                    "response": safe_responses[category],
                    "severity": severity,
                    "intent": intent
                })

            # Batch save to avoid freezing
            if len(synthetic_data) >= BATCH_SAVE:
                filename = f"hospital_batch_round{round_num}.jsonl"
                with open(filename, "a", encoding="utf-8") as f:
                    for row in synthetic_data:
                        json.dump(row, f, ensure_ascii=False)
                        f.write("\n")
                print(f"Saved batch {len(synthetic_data)} to {filename}")
                synthetic_data = []

# Save remaining
if synthetic_data:
    filename = "hospital_batch_final.jsonl"
    with open(filename, "a", encoding="utf-8") as f:
        for row in synthetic_data:
            json.dump(row, f, ensure_ascii=False)
            f.write("\n")
    print(f"Saved remaining {len(synthetic_data)} to {filename}")

# -------------------------------
# 7️⃣ Merge & Shuffle All Batch Files
# -------------------------------
all_files = [f for f in os.listdir(".") if f.startswith("hospital_batch") and f.endswith(".jsonl")]
merged_data = []

for file in all_files:
    with open(file, "r", encoding="utf-8") as f:
        for line in f:
            merged_data.append(json.loads(line))

random.shuffle(merged_data)

with open("hospital_full_merged.jsonl", "w", encoding="utf-8") as f:
    for row in merged_data:
        json.dump(row, f, ensure_ascii=False)
        f.write("\n")

print(f"\n Merged {len(merged_data)} questions into hospital_full_merged.jsonl")



# # hospital_data_generator.py

# from gpt4all import GPT4All
# import json
# import random
# import re


# # -------------------------------
# # 1️⃣ Base Categories & Prompts
# # -------------------------------

# base_prompts = {

#     "accident_fracture": [
#         "I broke my leg in an accident",
#         "I fell and my arm is swollen",
#         "I think my bone is fractured",
#         "I slipped and injured my back",
#         "My waist is hurting after falling",
#         "I can’t move my leg well"
#     ],

#     "malaria_fever": [
#         "I have malaria symptoms",
#         "I have high fever and chills",
#         "I’m sweating and very weak",
#         "My body is hot and painful",
#         "I feel cold and hot at the same time",
#         "I’m shivering with fever"
#     ],

#     "typhoid_infection": [
#         "Doctor said I may have typhoid",
#         "I have stomach pain and fever",
#         "I feel weak for weeks now",
#         "I vomit and feel tired",
#         "I can’t eat well for days",
#         "My body is always tired"
#     ],

#     "pregnancy": [
#         "I have bleeding in pregnancy",
#         "My baby is not moving",
#         "I have labor pain",
#         "I feel dizzy while pregnant",
#         "My stomach is tightening",
#         "I feel sharp pain in pregnancy"
#     ],

#     "bleeding_wound": [
#         "My wound is bleeding badly",
#         "I cut myself deeply",
#         "Blood is not stopping",
#         "I injured my leg badly",
#         "My hand is bleeding seriously",
#         "I lost much blood"
#     ],

#     "animal_bite": [
#         "A dog bit me",
#         "I was bitten by a snake",
#         "A cat scratched me badly",
#         "A rat bit my finger",
#         "A monkey scratched me",
#         "A stray dog attacked me"
#     ],

#     "swelling_infection": [
#         "My leg is swollen",
#         "My face is swollen",
#         "There is pus in my wound",
#         "My hand is infected",
#         "My toe is swollen",
#         "My ear is painful and swollen"
#     ],

#     "respiratory": [
#         "I am coughing badly",
#         "I have chest pain and cough",
#         "I can’t breathe well",
#         "I’m short of breath",
#         "My chest is tight",
#         "I wheeze when breathing"
#     ],

#     "digestive": [
#         "I have diarrhea",
#         "My stomach hurts badly",
#         "I vomit every day",
#         "I can’t eat well",
#         "I have running stomach",
#         "I feel nauseous"
#     ],

#     "appointment": [
#         "I want to see a doctor",
#         "Book appointment for me",
#         "I need lab test",
#         "Reschedule my visit",
#         "I want medical checkup",
#         "I need hospital appointment"
#     ]
# }


# # -------------------------------
# # 2️⃣ Safe Responses
# # -------------------------------

# safe_responses = {
#     "accident_fracture": "This sounds serious. Please avoid movement and visit the hospital immediately.",
#     "malaria_fever": "Please check your temperature and visit the hospital for malaria test.",
#     "typhoid_infection": "You may need laboratory tests. Please consult a doctor.",
#     "pregnancy": "This could be urgent. Please contact your healthcare provider immediately.",
#     "bleeding_wound": "Apply pressure and seek emergency medical care now.",
#     "animal_bite": "Please wash the area and visit the hospital for treatment and vaccines.",
#     "swelling_infection": "This may be an infection. Please see a doctor for treatment.",
#     "respiratory": "Breathing issues are serious. Please seek medical attention.",
#     "digestive": "Drink fluids and consult a doctor if symptoms persist.",
#     "appointment": "Sure, I can help you book your appointment."
# }


# # -------------------------------
# # 3️⃣ Severity Rules
# # -------------------------------

# high_risk = ["bleeding_wound", "pregnancy", "accident_fracture", "animal_bite"]
# medium_risk = ["malaria_fever", "typhoid_infection", "respiratory", "swelling_infection"]
# low_risk = ["digestive", "appointment"]


# # -------------------------------
# # 4️⃣ Load Model
# # -------------------------------

# model = GPT4All(
#     "mistral-7b-openorca.gguf2.Q4_0.gguf",
#     model_path="./models"
# )


# # -------------------------------
# # 5️⃣ Helper: Clean Lines
# # -------------------------------

# def clean_lines(text):
#     lines = []
#     for line in text.split("\n"):
#         line = re.sub(r"^[\-\d\.\•\s]+", "", line).strip()
#         if len(line) > 5:
#             lines.append(line)
#     return list(set(lines))


# # -------------------------------
# # 6️⃣ Generate Dataset
# # -------------------------------

# synthetic_data = []


# for category, prompts in base_prompts.items():

#     for base_text in prompts:

#         gen_prompt = f"""
# Generate 30 different ways a Nigerian patient might say this
# using simple English or pidgin:

# "{base_text}"

# Make them natural and realistic.
# Each on a new line.
# """

#         try:

#             response = model.generate(
#                 gen_prompt,
#                 max_tokens=800
#             )

#             variations = clean_lines(response)

#             if not variations:
#                 variations = [base_text]

#         except Exception as e:

#             print("Generation error:", e)
#             variations = [base_text]


#         for text in variations:

#             if category in high_risk:
#                 severity = "high"
#             elif category in medium_risk:
#                 severity = "medium"
#             else:
#                 severity = "low"


#             intent = "emergency" if severity == "high" else (
#                 "appointment" if category == "appointment" else "complaint"
#             )


#             synthetic_data.append({

#                 "prompt": text,
#                 "category": category,
#                 "response": safe_responses[category],
#                 "severity": severity,
#                 "intent": intent
#             })


# # -------------------------------
# # 7️⃣ Shuffle
# # -------------------------------

# random.shuffle(synthetic_data)


# # -------------------------------
# # 8️⃣ Save JSONL
# # -------------------------------

# with open("hospital_full_data.jsonl", "w", encoding="utf-8") as f:

#     for row in synthetic_data:
#         json.dump(row, f, ensure_ascii=False)
#         f.write("\n")


# print(f"\n Generated {len(synthetic_data)} medical questions")
# print("📁 Saved as hospital_full_data.jsonl\n")
