import glob
import json
import random

# 1️⃣ Collect all batch files
batch_files = sorted(glob.glob("hospital_data_batch*.jsonl"))  # includes final batch
all_data = []

# 2️⃣ Load all data from batches
for file in batch_files:
    with open(file, "r", encoding="utf-8") as f:
        for line in f:
            all_data.append(json.loads(line))

print(f"Merged {len(all_data)} questions from {len(batch_files)} batch files.")

# 3️⃣ Shuffle to mix categories
random.shuffle(all_data)

# 4️⃣ Save to a single file
with open("hospital_full_merged.jsonl", "w", encoding="utf-8") as f:
    for item in all_data:
        json.dump(item, f, ensure_ascii=False)
        f.write("\n")

print("✅ Saved all questions in hospital_full_merged.jsonl")
