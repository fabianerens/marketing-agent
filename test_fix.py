"""
Test fix: Force Developer API mode instead of Vertex AI.
"""

import os
from dotenv import load_dotenv
load_dotenv()

print("Testing Developer API mode fix...")
print("=" * 70)

api_key = os.getenv("GOOGLE_API_KEY")
print(f"API Key: {api_key[:20]}...{api_key[-4:]}\n")

# Test with explicit Developer API configuration
from google import genai

print("Creating client with EXPLICIT Developer API mode...")
try:
    # This forces Developer API mode (not Vertex AI)
    client = genai.Client(
        api_key=api_key,
        http_options={'api_version': 'v1'}  # Use v1, not v1beta
    )

    print("[OK] Client created\n")

    # Test models
    test_models = [
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-pro",
    ]

    for model_name in test_models:
        print(f"Testing: {model_name}")
        try:
            response = client.models.generate_content(
                model=model_name,
                contents="Say hello"
            )

            if response.text:
                print(f"  [SUCCESS] {model_name} works!")
                print(f"  Response: {response.text[:50]}")
                print(f"\n>>> USE THIS MODEL: {model_name}")
                print(f">>> USE THIS API VERSION: v1")
                break

        except Exception as e:
            error = str(e)
            if "404" in error:
                print(f"  [FAIL] Not found")
            else:
                print(f"  [ERROR] {error[:80]}")

except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
