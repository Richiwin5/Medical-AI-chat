from gpt4all import GPT4All
from transformers import pipeline


# GPT4All (Chat)
chat_model = GPT4All(
    "mistral-7b-openorca.gguf",
    model_path="./models"
)

# BioGPT (Medical)
bio_model = pipeline(
    "text-generation",
    model="microsoft/BioGPT"
)


def medical_explain(text):

    res = bio_model(text, max_length=200)
    return res[0]["generated_text"]


def chat_reply(prompt):

    return chat_model.generate(prompt, max_tokens=200)
