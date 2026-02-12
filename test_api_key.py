"""
Test if the Google API key is valid and can access Gemini.
"""

import os
from dotenv import load_dotenv
load_dotenv()

print("Testing Google AI API Key...")
print("=" * 70)

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("[ERROR] GOOGLE_API_KEY not found in .env")
    exit(1)

print(f"API Key: {api_key[:20]}...{api_key[-4:]}")
print()

# Test 1: Simple API call
print("Test 1: Direct API call with genai.Client")
print("-" * 70)

try:
    from google import genai

    client = genai.Client(api_key=api_key)

    # Try to generate content with a known model
    test_models = [
        "models/gemini-1.5-flash",
        "models/gemini-1.5-pro",
        "models/gemini-pro",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-pro",
    ]

    for model_name in test_models:
        print(f"\nTrying: {model_name}")
        try:
            response = client.models.generate_content(
                model=model_name,
                contents="Say 'Hello' in one word"
            )

            if response.text:
                print(f"  [SUCCESS] Model '{model_name}' works!")
                print(f"  Response: {response.text[:50]}")
                print(f"\n>>> USE THIS MODEL: {model_name}")
                break

        except Exception as e:
            error_str = str(e)
            if "404" in error_str:
                print(f"  [FAIL] Model not found")
            elif "403" in error_str:
                print(f"  [FAIL] Permission denied - check API key")
            else:
                print(f"  [ERROR] {error_str[:100]}")

except Exception as e:
    print(f"[ERROR] Failed to initialize client: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
