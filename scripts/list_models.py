import google.generativeai as genai
import os

# Configure your API key
# Ensure your GEMINI_API_KEY environment variable is set
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("ERROR: GEMINI_API_KEY environment variable not set. Please set it to your Gemini API key.")
    exit(1)

genai.configure(api_key=GEMINI_API_KEY)

print("Listing available Gemini models that support 'generateContent':")
for m in genai.list_models():
    if "generateContent" in m.supported_generation_methods:
        print(f"- {m.name} (Description: {m.description})")

print("\nListing ALL available Gemini models (including those not for generateContent):")
for m in genai.list_models():
    print(f"- {m.name} (Description: {m.description if hasattr(m, 'description') else 'No description'})")