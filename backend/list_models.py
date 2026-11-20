
import sys
import os
import google.generativeai as genai
from dotenv import load_dotenv

sys.path.append(os.getcwd())

load_dotenv(".env")
api_key = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=api_key)

with open("models.txt", "w") as f:
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                f.write(m.name + "\n")
    except Exception as e:
        f.write(f"Error: {e}")
