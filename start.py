"""
Simple startup test to verify the app can start.
"""

print("Starting YouTube Marketing Agent...")
print("=" * 50)

try:
    from app import create_app
    print("OK: Imports successful")

    app = create_app()
    print("OK: App created")

    print("\nLaunching Gradio UI...")
    print("The app will be available at: http://localhost:7860")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 50)

    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
    )

except KeyboardInterrupt:
    print("\n\nShutting down...")
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
