"""
Test the API key with direct REST API call (bypassing SDK).
"""

import os
import requests
from dotenv import load_dotenv
load_dotenv()

print("Testing API key with direct REST API...")
print("=" * 70)

api_key = os.getenv("GOOGLE_API_KEY")
print(f"API Key: {api_key[:20]}...{api_key[-4:]}\n")

# Direct REST API call to Gemini
url = f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={api_key}"

headers = {
    "Content-Type": "application/json"
}

data = {
    "contents": [{
        "parts": [{
            "text": "Say hello in one word"
        }]
    }]
}

print(f"POST {url[:80]}...\n")

try:
    response = requests.post(url, headers=headers, json=data, timeout=10)

    print(f"Status Code: {response.status_code}")
    print(f"Response:\n{response.text[:500]}\n")

    if response.status_code == 200:
        print("[SUCCESS] API key is valid!")
        print(">>> The problem is NOT the API key itself")
        print(">>> The problem is how ADK/genai SDK uses it")
    elif response.status_code == 400:
        print("[WARNING] Bad request - but API key accepted")
    elif response.status_code == 403:
        print("[ERROR] API key is invalid or lacks permissions")
    elif response.status_code == 404:
        print("[ERROR] Model not found with this key")
    else:
        print(f"[ERROR] Unexpected status code")

except Exception as e:
    print(f"[ERROR] {e}")

print("=" * 70)
