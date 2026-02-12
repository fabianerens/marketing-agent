"""
Test which Gemini models work with ADK.
"""

import os
from dotenv import load_dotenv
load_dotenv()

from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import InMemoryRunner

# Test different model names
test_models = [
    "gemini-1.5-flash-latest",
    "gemini-1.5-flash",
    "gemini-1.5-pro-latest",
    "gemini-1.5-pro",
    "gemini-pro",
]

print("Testing Gemini models with ADK...")
print("=" * 60)

working_model = None

for model_name in test_models:
    print(f"\nTesting: {model_name}")
    try:
        agent = LlmAgent(
            model=model_name,
            name='test_agent',
            description="Test agent",
            instruction="You are a test agent. Say 'Hello!'",
        )

        runner = InMemoryRunner(
            agent=agent,
            app_name="test"
        )

        print(f"  [OK] Model '{model_name}' initialized successfully!")
        print(f"  >> Using this model should work.")
        working_model = model_name
        break

    except Exception as e:
        error_str = str(e)
        if "404" in error_str or "NOT_FOUND" in error_str:
            print(f"  [FAIL] Model not found: {model_name}")
        else:
            print(f"  [ERROR] {error_str[:150]}")

print("\n" + "=" * 60)
if working_model:
    print(f"SUCCESS: Use model '{working_model}' in your .env file")
    print(f"\nUpdate .env:")
    print(f"GEMINI_MODEL={working_model}")
else:
    print("ERROR: No working model found!")
print("=" * 60)
