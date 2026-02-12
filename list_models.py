"""
List all available Gemini models for your API key.
"""

import os
from dotenv import load_dotenv
load_dotenv()

from google import genai

print("Listing available Gemini models...")
print("=" * 70)

try:
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

    print("\nFetching models from Google AI API...\n")

    models = client.models.list()

    gemini_models = []

    for model in models:
        model_name = model.name
        if 'gemini' in model_name.lower():
            # Check if it supports generateContent
            methods = getattr(model, 'supported_generation_methods', [])
            if 'generateContent' in str(methods):
                gemini_models.append(model_name)
                print(f"[OK] {model_name}")
                print(f"     Methods: {methods}")
                print()

    print("=" * 70)
    print(f"\nFound {len(gemini_models)} compatible Gemini models:")
    for model in gemini_models:
        print(f"  - {model}")

    if gemini_models:
        # Extract just the model ID (remove "models/" prefix if present)
        recommended = gemini_models[0]
        if recommended.startswith("models/"):
            recommended = recommended.replace("models/", "")

        print(f"\nRECOMMENDED: Use this in your .env:")
        print(f"GEMINI_MODEL={recommended}")

except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()

print("=" * 70)
