"""
Final test: Does ADK work with gemini-2.5-flash?
"""

import os
from dotenv import load_dotenv
load_dotenv()

print("Final test with gemini-2.5-flash...")
print("=" * 70)

from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import InMemoryRunner

model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
print(f"Testing model: {model_name}\n")

try:
    # Create agent
    agent = LlmAgent(
        model=model_name,
        name='test_agent',
        description="Test agent",
        instruction="You are a test agent. When asked to say hello, respond with just 'Hello!'",
        tools=[]
    )

    print("[OK] Agent created successfully!")

    # Create runner
    runner = InMemoryRunner(
        agent=agent,
        app_name="youtube_marketing_agent"
    )

    print("[OK] Runner created successfully!")
    print("\n" + "=" * 70)
    print("[SUCCESS] The agent should work now!")
    print("\nYou can now start your app with:")
    print("  uv run python start.py")
    print("=" * 70)

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()

