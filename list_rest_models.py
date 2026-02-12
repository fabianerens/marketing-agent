"""
List available models via REST API.
"""

import os
import requests
from dotenv import load_dotenv
load_dotenv()

print("Listing available models via REST API...")
print("=" * 70)

api_key = os.getenv("GOOGLE_API_KEY")
print(f"API Key: {api_key[:20]}...{api_key[-4:]}\n")

# List models endpoint
url = f"https://generativelanguage.googleapis.com/v1/models?key={api_key}"

print(f"GET {url[:80]}...\n")

try:
    response = requests.get(url, timeout=10)

    print(f"Status Code: {response.status_code}\n")

    if response.status_code == 200:
        data = response.json()
        models = data.get('models', [])

        print(f"Found {len(models)} models:\n")

        gemini_models = []
        for model in models:
            name = model.get('name', '')
            supported_methods = model.get('supportedGenerationMethods', [])

            if 'gemini' in name.lower():
                print(f"  - {name}")
                print(f"    Methods: {', '.join(supported_methods)}")
                if 'generateContent' in supported_methods:
                    gemini_models.append(name)
                    print(f"    [OK] Supports generateContent")
                print()

        print("=" * 70)
        if gemini_models:
            print(f"\nWORKING MODELS ({len(gemini_models)}):")
            for model in gemini_models:
                # Strip "models/" prefix if present
                model_id = model.replace("models/", "")
                print(f"  {model_id}")

            print(f"\n>>> UPDATE YOUR .env WITH:")
            print(f"GEMINI_MODEL={gemini_models[0].replace('models/', '')}")
        else:
            print("\n[ERROR] No Gemini models with generateContent support found!")
            print("This API key may not have access to Gemini models.")

    elif response.status_code == 403:
        print("[ERROR] Permission denied!")
        print("This API key may not be valid or activated.")
        print(response.text)

    else:
        print(f"[ERROR] Status {response.status_code}")
        print(response.text[:500])

except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()

print("=" * 70)
