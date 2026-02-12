"""
YouTube Marketing Analysis Agent - Main Launcher.

This app analyzes YouTube channels to identify successful video formats
and provides AI-powered marketing recommendations using Google ADK.
"""

import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import and launch Gradio app
from app import create_app, get_css, get_theme

if __name__ == "__main__":
    app = create_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        css=get_css(),
        theme=get_theme(),
    )
