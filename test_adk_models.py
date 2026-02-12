"""
Test ADK with different model names to find what works.
"""

import os
from dotenv import load_dotenv
load_dotenv()

print("Testing ADK model compatibility...")
print("=" * 70)

# These are the model names to test
test_models = [
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
    "gemini-1.5-pro",
    "gemini-1.5-pro-latest",
    "gemini-pro",
    "gemini-1.0-pro",
    "models/gemini-1.5-flash",
    "models/gemini-1.5-pro",
]

from google.adk.agents.llm_agent import LlmAgent

working_models = []

for model_name in test_models:
    print(f"\nTrying: {model_name}")
    try:
        # Just create the agent - don't run it
        agent = LlmAgent(
            model=model_name,
            name='test_agent',
            description="Test",
            instruction="Say hello",
            tools=[]
        )
        print(f"  [SUCCESS] Agent created with model: {model_name}")
        working_models.append(model_name)

    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg or "NOT_FOUND" in error_msg:
            print(f"  [FAIL] Model not found")
        elif "API" in error_msg:
            print(f"  [FAIL] API error: {error_msg[:80]}")
        else:
            print(f"  [ERROR] {error_msg[:80]}")

print("\n" + "=" * 70)
print(f"\nWorking models: {len(working_models)}")
for model in working_models:
    print(f"  - {model}")

if working_models:
    print(f"\nRECOMMENDATION: Use '{working_models[0]}' in your .env")
else:
    print("\nERROR: No compatible models found!")
    print("This might be an API key or permissions issue.")
print("=" * 70)
