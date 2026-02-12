"""
Gradio UI for YouTube Marketing Analysis Agent.

Features:
- Channel input (URL/@handle/ID)
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
        channel_input: Channel URL/@handle/ID
        max_videos: Maximum videos to analyze
        days_back: Days back filter (or None)
        like_weight: Like weight for engagement
        comment_weight: Comment weight for engagement
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
    comment_weight: float,
    exclude_keywords: str,
    min_views: int,
    marketing_goal: str,
) -> Tuple[str, str, str]:
    """
    Synchronous wrapper for Gradio.

    Returns:
        Tuple of (status_message, analysis_markdown, error_message)
    """
    # Validation
    if not channel_input or not channel_input.strip():
        return (
            "❌ Error",
            "",
            "Please enter a valid YouTube channel URL, @handle, or channel ID.",
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
                "The channel identifier could not be resolved. Please check the URL/@handle/ID.",
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


def create_app() -> gr.Blocks:
    """
    Create the Gradio app.

    Returns:
        Gradio Blocks app
    """
    with gr.Blocks(title="YouTube Marketing Agent", theme=gr.themes.Soft()) as app:
        gr.Markdown(
            """
        # 🎬 YouTube Marketing Analysis Agent

        **Powered by Google ADK + YouTube Data API v3**

        Analyze YouTube channels to identify successful video formats and get AI-powered
        marketing recommendations.

        This agent:
        - Fetches real YouTube data (views, likes, comments, duration)
        - Calculates engagement KPIs (view velocity, engagement score)
        - Identifies recurring format patterns (series, themes, duration buckets)
        - Generates actionable recommendations using Gemini AI
        """
        )

        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown("### 📊 Analysis Configuration")

                channel_input = gr.Textbox(
                    label="YouTube Channel",
                    placeholder="Enter URL, @handle, or channel ID (e.g., @MrBeast)",
                    info="Supports: youtube.com/channel/UCxxx, @username, or direct channel ID",
                )

                with gr.Row():
                    max_videos = gr.Slider(
                        label="Max Videos to Analyze",
                        minimum=5,
                        maximum=100,
                        value=30,
                        step=5,
                        info="More videos = better patterns, but slower analysis",
                    )

                    days_back = gr.Number(
                        label="Days Back (Optional)",
                        value=None,
                        precision=0,
                        info="Leave empty for all videos, or set to analyze recent videos only",
                    )

                gr.Markdown("### ⚖️ KPI Weights")
                gr.Markdown("Adjust how engagement score is calculated:")

                with gr.Row():
                    like_weight = gr.Slider(
                        label="Like Weight",
                        minimum=0.0,
                        maximum=1.0,
                        value=0.6,
                        step=0.1,
                    )

                    comment_weight = gr.Slider(
                        label="Comment Weight",
                        minimum=0.0,
                        maximum=1.0,
                        value=0.4,
                        step=0.1,
                    )

                gr.Markdown("### 🔍 Filters")

                exclude_keywords = gr.Textbox(
                    label="Exclude Keywords (Optional)",
                    placeholder="e.g., trailer, teaser, announcement",
                    info="Comma-separated keywords to exclude from analysis",
                )

                min_views = gr.Number(
                    label="Minimum Views",
                    value=0,
                    precision=0,
                    info="Filter out videos below this view count",
                )

                marketing_goal = gr.Textbox(
                    label="Marketing Goal (Optional)",
                    placeholder="e.g., Increase subscriber growth, Boost engagement on tech reviews",
                    lines=2,
                    info="Describe your goal for contextualized recommendations",
                )

                analyze_btn = gr.Button("🚀 Analyze Channel", variant="primary", size="lg")

            with gr.Column(scale=3):
                gr.Markdown("### 📈 Results")

                status_output = gr.Markdown(
                    value="*Ready to analyze. Configure parameters and click 'Analyze Channel'.*"
                )

                error_output = gr.Markdown(value="", visible=True)

                analysis_output = gr.Markdown(value="", visible=True)

        # Examples
        gr.Markdown("### 💡 Example Channels")
        gr.Examples(
            examples=[
                ["@MrBeast", 30, None, 0.6, 0.4, "", 0, "General viral content analysis"],
                ["@MKBHD", 25, 90, 0.7, 0.3, "", 10000, "Tech product review optimization"],
                ["@3blue1brown", 20, None, 0.5, 0.5, "", 0, "Educational content patterns"],
                ["https://www.youtube.com/channel/UCsooa4yRKGN_zEE8iknghZA", 30, None, 0.6, 0.4, "", 0, ""],
            ],
            inputs=[
                channel_input,
                max_videos,
                days_back,
                like_weight,
                comment_weight,
                exclude_keywords,
                min_views,
                marketing_goal,
            ],
        )

        # Event handlers
        analyze_btn.click(
            fn=analyze_channel_sync,
            inputs=[
                channel_input,
                max_videos,
                days_back,
                like_weight,
                comment_weight,
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
            """
        ---

        **Note**: This tool uses the YouTube Data API v3 which has quota limits.
        Analysis is cached for 12 hours to minimize API usage.

        **Data Source**: Public YouTube metrics (views, likes, comments, video metadata)

        **Disclaimer**: Past performance doesn't guarantee future success. Use insights as
        guidance, not absolute rules. Always respect YouTube's Terms of Service.
        """
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
