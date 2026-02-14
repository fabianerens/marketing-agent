"""
Gradio UI for YouTube Marketing Analysis Agent.

Features:
- Channel input (URL)
- Analysis parameters (max videos, date range, KPI weights, filters)
- Results display (markdown summary, video table, format clusters)
- Refinement section (adjust parameters and re-run)
- Error handling with user-friendly messages
"""

import os
import asyncio
import logging
from typing import Dict, Any, Tuple, Optional

import gradio as gr
from dotenv import load_dotenv
from google.genai import types

from agent import root_runner

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


def _extract_text_from_event(event: Any) -> str:
    """
    Robustly extract text from ADK/google-genai streaming events across versions.

    Older code used `event.text_part.text`, but newer event schemas may expose
    text via `event.text`, `event.delta.text`, or `event.content.parts[*].text`.
    """
    # 1) Some versions expose direct text
    txt = getattr(event, "text", None)
    if isinstance(txt, str) and txt:
        return txt

    # 2) Some streaming events expose delta text
    delta = getattr(event, "delta", None)
    if delta is not None:
        delta_text = getattr(delta, "text", None)
        if isinstance(delta_text, str) and delta_text:
            return delta_text

    # 3) Some versions expose content.parts[*].text
    content = getattr(event, "content", None)
    parts = getattr(content, "parts", None) if content is not None else None
    if parts:
        out = []
        for p in parts:
            p_text = getattr(p, "text", None)
            if isinstance(p_text, str) and p_text:
                out.append(p_text)
        if out:
            return "".join(out)

    # 4) Legacy schema (what your code used before)
    text_part = getattr(event, "text_part", None)
    if text_part is not None:
        tp_text = getattr(text_part, "text", None)
        if isinstance(tp_text, str) and tp_text:
            return tp_text

    return ""


async def analyze_channel_async(
    channel_input: str,
    max_videos: int,
    days_back: Optional[int],
    like_weight: float,
    comment_weight: float,
    exclude_keywords: str,
    min_views: int,
    marketing_goal: str,
) -> Dict[str, Any]:
    """
    Run the agent analysis asynchronously.

    Args:
        channel_input: Channel URL
        max_videos: Maximum videos to analyze
        days_back: Days back filter (or None)
        like_weight: Like weight for engagement (0-1)
        comment_weight: Comment weight for engagement (calculated as 1 - like_weight)
        exclude_keywords: Comma-separated keywords to exclude
        min_views: Minimum view count
        marketing_goal: User's marketing goal

    Returns:
        Results dictionary from agent
    """
    # Parse exclude keywords
    exclude_keywords_list = (
        [kw.strip() for kw in exclude_keywords.split(",") if kw.strip()]
        if exclude_keywords
        else []
    )

    # Build user message
    user_message = f"""
Analyze the YouTube channel: {channel_input}

Analysis Parameters:
- Maximum videos: {max_videos}
- Days back: {days_back if days_back else "All videos"}
- KPI weights: Like={like_weight}, Comment={comment_weight}
- Exclude keywords: {exclude_keywords_list if exclude_keywords_list else "None"}
- Minimum views: {min_views}
- Marketing goal: {marketing_goal if marketing_goal else "General analysis"}

Please provide a comprehensive analysis with top-performing formats and recommendations.
"""

    # Create session
    session = await root_runner.session_service.create_session(
        user_id="gradio_user",
        app_name="youtube_marketing_agent",
    )

    # Create content
    content = types.Content(role="user", parts=[types.Part(text=user_message)])

    # Run agent (streaming)
    events_async = root_runner.run_async(
        user_id="gradio_user",
        session_id=session.id,
        new_message=content,
    )

    # Collect response
    full_response = ""
    async for event in events_async:
        full_response += _extract_text_from_event(event)

    return {
        "response": full_response,
        "session_id": session.id,
    }


def analyze_channel_sync(
    channel_input: str,
    max_videos: int,
    days_back: Optional[int],
    like_weight: float,
    exclude_keywords: str,
    min_views: int,
    marketing_goal: str,
) -> Tuple[str, str, str]:
    """
    Synchronous wrapper for Gradio.

    Returns:
        Tuple of (status_message, analysis_markdown, error_message)
    """
    # Calculate comment weight from like weight
    comment_weight = 1.0 - like_weight
    # Validation
    if not channel_input or not channel_input.strip():
        return (
            "❌ Error",
            "",
            "Please enter a valid YouTube channel URL",
        )

    # Check API keys
    if not os.getenv("YOUTUBE_API_KEY"):
        return (
            "❌ Configuration Error",
            "",
            "YOUTUBE_API_KEY not configured. Please add it to your .env file.",
        )

    if not os.getenv("GOOGLE_API_KEY"):
        return (
            "❌ Configuration Error",
            "",
            "GOOGLE_API_KEY not configured. Please add it to your .env file.",
        )

    try:
        # Run analysis
        result = asyncio.run(
            analyze_channel_async(
                channel_input=channel_input.strip(),
                max_videos=max_videos,
                days_back=days_back if days_back and days_back > 0 else None,
                like_weight=like_weight,
                comment_weight=comment_weight,
                exclude_keywords=exclude_keywords,
                min_views=min_views,
                marketing_goal=marketing_goal,
            )
        )

        # Extract response
        analysis_text = result.get("response", "")

        if not analysis_text:
            return (
                "❌ Analysis Failed",
                "",
                "The agent did not return any results. Please try again.",
            )

        # Check for common error patterns
        if "INVALID_CHANNEL" in analysis_text or "Could not resolve" in analysis_text:
            return (
                "❌ Invalid Channel",
                analysis_text,
                "The channel identifier could not be resolved. Please check the URL.",
            )

        if "NO_VIDEOS" in analysis_text or "No videos found" in analysis_text:
            return (
                "⚠️ No Videos Found",
                analysis_text,
                "No videos were found matching your criteria. Try adjusting the filters.",
            )

        if "quota" in analysis_text.lower() or "API_ERROR" in analysis_text:
            return (
                "❌ API Error",
                analysis_text,
                "YouTube API quota exceeded or API error. Please try again later.",
            )

        # Success
        return (
            "✅ Analysis Complete",
            analysis_text,
            "",
        )

    except Exception as e:
        logger.error(f"Error in analysis: {e}", exc_info=True)
        return (
            "❌ Unexpected Error",
            "",
            f"An unexpected error occurred: {str(e)}\n\nPlease check your configuration and try again.",
        )


# Lighthouse-inspired CSS
CUSTOM_CSS = """
/* Base */
body, .gradio-container, .main, .contain, .app {
    background-color: #faf9f7 !important;
}

.gradio-container {
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif !important;
    max-width: 100% !important;
    margin: 0 !important;
    padding: 48px 80px !important;
    color: #1a1a1a !important;
}

/* All text black */
.gradio-container,
.gradio-container p,
.gradio-container span,
.gradio-container label,
.gradio-container div,
.gradio-container h1,
.gradio-container h2,
.gradio-container h3,
.gradio-container h4,
.gradio-container li,
.gradio-container strong,
.gradio-container em,
.gradio-container code,
.gradio-container pre,
.gradio-container .prose,
.gradio-container .prose *,
.gradio-container .markdown-text,
.gradio-container .markdown-text * {
    color: #1a1a1a !important;
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif !important;
}

/* Header */
.header-section h1 {
    font-size: 1.25rem !important;
    font-weight: 500 !important;
    color: #1a1a1a !important;
    margin: 0 !important;
    padding-bottom: 20px !important;
    border-bottom: 1px solid #1a1a1a !important;
}

/* Hero Text */
.hero-section p {
    font-size: 1.75rem !important;
    line-height: 1.4 !important;
    font-weight: 400 !important;
    color: #1a1a1a !important;
    margin: 48px 0 !important;
    letter-spacing: -0.01em !important;
}

/* Section Labels */
.section-label p {
    font-size: 0.875rem !important;
    color: #1a1a1a !important;
    margin-bottom: 24px !important;
}

/* Form Container */
.form-section {
    max-width: 600px !important;
    margin: 0 auto 32px auto !important;
}

/* Form field spacing */
.form-section > div {
    margin-bottom: 20px !important;
}

.form-section .row {
    gap: 16px !important;
    margin-bottom: 20px !important;
}

/* Remove Gradio backgrounds */
.gradio-container .block,
.gradio-container .form,
.gradio-container .wrap {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

/* Labels */
.gradio-container label span {
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    color: #1a1a1a !important;
}

/* Inputs */
.gradio-container input[type="text"],
.gradio-container textarea {
    background: #fff !important;
    border: 1px solid #1a1a1a !important;
    border-radius: 4px !important;
    padding: 12px 14px !important;
    font-size: 1rem !important;
    color: #1a1a1a !important;
}

.gradio-container input[type="text"]:focus,
.gradio-container textarea:focus {
    border-color: #1a1a1a !important;
    outline: none !important;
}

/* Number Input */
.gradio-container input[type="number"] {
    background: #fff !important;
    border: 1px solid #1a1a1a !important;
    border-radius: 4px !important;
    padding: 10px 12px !important;
    color: #1a1a1a !important;
}

/* Sliders */
.gradio-container input[type="range"] {
    accent-color: #1a1a1a !important;
}

/* Button */
.gradio-container button.primary {
    background: #1a1a1a !important;
    color: #fff !important;
    border: none !important;
    border-radius: 4px !important;
    padding: 14px 28px !important;
    font-size: 0.9rem !important;
    font-weight: 500 !important;
    cursor: pointer !important;
    width: 100% !important;
    max-width: 600px !important;
    margin: 16px auto 0 auto !important;
    display: block !important;
}

.gradio-container button.primary:hover {
    background: #333 !important;
}

/* Results Section */
.results-section {
    margin-top: 48px !important;
    padding-top: 32px !important;
    border-top: 1px solid #e0e0e0 !important;
    max-width: 600px !important;
    margin-left: auto !important;
    margin-right: auto !important;
}

/* Footer */
.footer-section {
    margin-top: 48px !important;
    padding-top: 24px !important;
    border-top: 1px solid #e0e0e0 !important;
    max-width: 600px !important;
    margin-left: auto !important;
    margin-right: auto !important;
}

.footer-section p {
    font-size: 0.8rem !important;
    color: #1a1a1a !important;
    line-height: 1.6 !important;
}

/* Hide Gradio footer */
footer {
    display: none !important;
}

/* Info text */
.gradio-container .info,
.gradio-container span[data-testid="info"] {
    font-size: 0.8rem !important;
    color: #1a1a1a !important;
}
"""


def get_css():
    """Return the custom CSS."""
    return CUSTOM_CSS


def get_theme():
    """Return the theme."""
    return gr.themes.Base()


def create_app() -> gr.Blocks:
    """
    Create the Gradio app with Lighthouse-inspired design.

    Returns:
        Gradio Blocks app
    """
    with gr.Blocks(title="YouTube Marketing Agent") as app:
        # Header
        gr.Markdown("# Marketing Agent", elem_classes=["header-section"])

        # Hero Text
        gr.Markdown(
            "Wir analysieren YouTube-Kanäle, um erfolgreiche Videoformate zu identifizieren. "
            "Als Grundlage für datengetriebene Marketingentscheidungen und nachhaltigen Erfolg.",
            elem_classes=["hero-section"],
        )

        # Form - Centered
        with gr.Column(elem_classes=["form-section"]):
            channel_input = gr.Textbox(
                label="YouTube Channel",
                placeholder="URL",
                info="z.B. GQ: https://www.youtube.com/@GQVideos",
            )

            max_videos = gr.Slider(
                label="Max Videos",
                minimum=5,
                maximum=100,
                value=30,
                step=5,
            )

            days_back = gr.Number(
                label="Tage zurück",
                value=None,
                precision=0,
                info="Leer = alle Videos",
            )

            like_weight = gr.Slider(
                label="Gewichtung (Likes ↔ Kommentare)",
                minimum=0.0,
                maximum=1.0,
                value=0.6,
                step=0.1,
                info="0 = nur Kommentare, 1 = nur Likes",
            )

            exclude_keywords = gr.Textbox(
                label="Keywords ausschließen",
                placeholder="z.B. trailer, teaser, announcement",
            )

            min_views = gr.Number(
                label="Minimum Views",
                value=0,
                precision=0,
            )

            marketing_goal = gr.Textbox(
                label="Marketing Ziel",
                placeholder="z.B. Subscriber-Wachstum steigern",
                lines=2,
            )

            analyze_btn = gr.Button("Analyse starten", variant="primary", size="lg")

        # Results - Below, Centered
        with gr.Column(elem_classes=["results-section"]):
            gr.Markdown("Ergebnisse", elem_classes=["section-label"])

            status_output = gr.Markdown(value="*Bereit für Analyse.*")
            error_output = gr.Markdown(value="")
            analysis_output = gr.Markdown(value="")

        # Event handler
        analyze_btn.click(
            fn=analyze_channel_sync,
            inputs=[
                channel_input,
                max_videos,
                days_back,
                like_weight,
                exclude_keywords,
                min_views,
                marketing_goal,
            ],
            outputs=[
                status_output,
                analysis_output,
                error_output,
            ],
        )

        # Footer
        gr.Markdown(
            "Hinweis: Diese Analyse nutzt die YouTube Data API v3. "
            "Die Ergebnisse dienen als Orientierung.",
            elem_classes=["footer-section"],
        )

    return app


def main():
    """Launch the Gradio app."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create and launch app
    app = create_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
    )


if __name__ == "__main__":
    main()
