"""
Streamlit UI for Video Analysis and Repair Assistance
Analyzes videos to identify appliance defects and provides repair instructions with source citations.
"""

import asyncio
import html
import json
import logging
import time
from typing import Optional
from fastapi import HTTPException
import httpx
import streamlit as st
import streamlit.components.v1 as components

# Configure logging
logger = logging.getLogger(__name__)

# Lazy imports to avoid loading heavy modules at startup
# These will be imported when first needed
_lazy_modules = {}

def _get_settings():
    """Lazy import for settings."""
    from app.settings import get_settings
    return get_settings()

def _analyze_video_with_gemini(*args, **kwargs):
    """Lazy import for Gemini video analysis."""
    from app.gemini_video_understanding import analyze_video_with_gemini
    return analyze_video_with_gemini(*args, **kwargs)

def _get_gemini_api_error():
    """Lazy import for GeminiAPIError."""
    from app.gemini_video_understanding import GeminiAPIError
    return GeminiAPIError

def _extract_user_questions(*args, **kwargs):
    """Lazy import for question extraction."""
    from app.question_generation import extract_user_questions
    return extract_user_questions(*args, **kwargs)

def _generate_clarifying_questions(*args, **kwargs):
    """Lazy import for clarifying questions."""
    from app.question_generation import generate_clarifying_questions
    return generate_clarifying_questions(*args, **kwargs)

def _build_retrieval_queries(*args, **kwargs):
    """Lazy import for retrieval queries."""
    from app.question_generation import build_retrieval_queries
    return build_retrieval_queries(*args, **kwargs)

# def _retrieve_support_docs(*args, **kwargs):
#     """Lazy import for RAG retrieval. Returns empty list if ChromaDB not available."""
#     try:
#         from app.rag_orchestrator import retrieve_support_docs
#         return retrieve_support_docs(*args, **kwargs)
#     except ImportError as e:
#         logger.warning(f"RAG not available (ChromaDB/sentence-transformers not installed): {e}")
#         return []  # Return empty list if dependencies missing
#     except Exception as e:
#         logger.warning(f"RAG retrieval failed: {e}")
#         return []  # Return empty list if RAG fails

def _compose_grounded_prompt(*args, **kwargs):
    """Lazy import for grounded prompt composition."""
    from app.rag_orchestrator import compose_grounded_prompt
    return compose_grounded_prompt(*args, **kwargs)

def _start_text_only_conversation(*args, **kwargs):
    """Lazy import for starting text-only conversation."""
    from app.elevenlabs_chatonly import start_text_only_conversation
    return start_text_only_conversation(*args, **kwargs)

def _anonymize_multiple_docs(*args, **kwargs):
    """Lazy import for document anonymization."""
    from app.elevenlabs_chatonly import anonymize_multiple_docs
    return anonymize_multiple_docs(*args, **kwargs)

def _answer_with_gemini(*args, **kwargs):
    """Lazy import for Gemini answering."""
    from app.rag_orchestrator import answer_with_gemini
    return answer_with_gemini(*args, **kwargs)

def _text_to_speech_wav(*args, **kwargs):
    """Lazy import for TTS."""
    from app.elevenlabs_tts import text_to_speech_wav
    return text_to_speech_wav(*args, **kwargs)

def _get_elevenlabs_tts_error():
    """Lazy import for ElevenLabsTTSError."""
    from app.elevenlabs_tts import ElevenLabsTTSError
    return ElevenLabsTTSError

def _get_video_errors():
    """Lazy import for video errors."""
    from app.video_io import VideoDownloadError, VideoTooLargeError
    return VideoDownloadError, VideoTooLargeError

def _download_video(*args, **kwargs):
    """Lazy import for video download."""
    from app.video_io import download_video
    return download_video(*args, **kwargs)

def _get_elevenlabs_agent_error():
    """Lazy import for ElevenLabsAgentError."""
    from app.elevenlabs_agent import ElevenLabsAgentError
    return ElevenLabsAgentError

# Aliases for compatibility (these are now handled via lazy imports)

# Page configuration
st.set_page_config(
    page_title="Video Repair Assistant",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border-left: 4px solid #17a2b8;
        margin: 1rem 0;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        display: flex;
        align-items: flex-start;
    }
    .chat-message.user {
        background-color: #e3f2fd;
        margin-left: 20%;
    }
    .chat-message.agent {
        background-color: #f1f8e9;
        margin-right: 20%;
    }
    .citation-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        margin: 0.25rem;
        border-radius: 0.25rem;
        background-color: #fff3cd;
        font-size: 0.85rem;
        border: 1px solid #ffc107;
    }
    .knowledge-base-info {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8f9fa;
        border-left: 4px solid #6c757d;
        margin: 1rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def run_async(coro):
    """Run async function in Streamlit's sync context."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


def process_video_assistance(media_bytes: bytes, mime_type: str, language: str, user_hint: Optional[str] = None, part_number: Optional[str] = None, is_image: bool = False):
    """Process video/image through the full assistance pipeline."""
    settings = _get_settings()
    
    if not settings.gemini_api_key:
        raise ValueError("Missing GEMINI_API_KEY. Please set it in your .env file or environment variables.")
    
    # Step 1: Media analysis
    media_type = "image" if is_image else "video"
    with st.status(f"🎥 Analyzing {media_type} with AI...", expanded=True) as status:
        status.update(label=f"🎥 Analyzing {media_type} with Gemini AI...", state="running")
        result = _analyze_video_with_gemini(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
            video_bytes=media_bytes,
            video_mime_type=mime_type,
            language=language,
            user_hint=user_hint,
            is_image=is_image,
        )
        analysis = result.data or {}
        transcript = analysis.get("transcript", "") or ""
        status.update(label="✅ Video analysis complete", state="complete")
    
    # Step 2: Question generation
    with st.status("❓ Generating questions...", expanded=False) as status:
        status.update(label="❓ Extracting questions from transcript...", state="running")
        user_questions = _extract_user_questions(transcript)
        clarifying_questions = _generate_clarifying_questions(
            appliance_type=analysis.get("appliance_type"),
            brand_or_model=analysis.get("brand_or_model"),
            issue_summary=analysis.get("issue_summary"),
            language=language,
        )
        status.update(label="✅ Questions generated", state="complete")
    
    # Step 3: Retrieval
    with st.status("📚 Generating grounded answer...", expanded=False) as status:
        status.update(label="📚 Searching knowledge base...", state="running")
        queries = _build_retrieval_queries(
            appliance_type=analysis.get("appliance_type"),
            brand_or_model=analysis.get("brand_or_model"),
            issue_summary=analysis.get("issue_summary"),
            user_questions=user_questions,
        )
        # Use part_number from user input if provided, otherwise from video analysis
        effective_part_number = part_number if part_number and part_number.strip() else analysis.get("part_number")
        # citations = _retrieve_support_docs(queries, part_number=effective_part_number)
        # status.update(label=f"✅ Found {len(citations)} relevant sources", state="complete")
    
    # Step 4: Generate grounded answer
    with st.status("💡 Generating repair instructions...", expanded=False) as status:
        status.update(label="💡 Generating detailed repair instructions ...", state="running")
        grounded_prompt = _compose_grounded_prompt(
            transcript=transcript,
            analysis=analysis,
            clarifying_questions=clarifying_questions,
            language=language,
            part_number=effective_part_number,
        )
        if settings.elevenlabs_txt_agent_id == "":
            raise HTTPException(status_code=400, detail="ELEVENLABS_TXT_AGENT_ID is required for text-only agent")
        
        agent_response = _start_text_only_conversation(
            settings.elevenlabs_api_key_write,
            settings.elevenlabs_txt_agent_id,
            grounded_prompt,  
        )
        full_text = "".join(agent_response)

        text, doc_id = _anonymize_multiple_docs(full_text, settings.elevenlabs_api_key_write)
        
        answer = {
            "text": text,
            "follow_up_questions": analysis.get("questions_to_confirm") or clarifying_questions,
        }
        status.update(label="✅ Repair instructions ready", state="complete")
    
    # Step 5: Generate audio from answer text
    audio_bytes = None
    audio_format = None
    if settings.elevenlabs_api_key:
        with st.status("🔊 Generating audio...", expanded=False) as status:
            status.update(label="🔊 Converting text to speech...", state="running")
            try:
                answer_text = answer.get("text", "")
                if answer_text:
                    audio_bytes, audio_format = _text_to_speech_wav(
                        text=answer_text,
                        api_key=settings.elevenlabs_api_key,
                        language=language,
                    )
                    status.update(label="✅ Audio generated", state="complete")
                else:
                    status.update(label="⚠️ No text to convert", state="complete")
            except Exception as e:
                if "ElevenLabsTTSError" in type(e).__name__:
                    status.update(label=f"⚠️ Audio generation failed: {str(e)}", state="error")
                    logger.warning(f"ElevenLabs TTS error: {str(e)}")
                else:
                    raise
            except Exception as e:
                status.update(label=f"⚠️ Audio generation error: {str(e)}", state="error")
                logger.warning(f"Unexpected TTS error: {str(e)}")
    
    # Prepare follow-up questions
    follow_ups = analysis.get("questions_to_confirm") or clarifying_questions
    
    return {
        "analysis": analysis,
        "transcript": transcript,
        "user_questions": user_questions,
        "clarifying_questions": clarifying_questions,
        "citations": [],  
        "answer": answer,
        "follow_up_questions": follow_ups,
        "audio_bytes": audio_bytes,
        "audio_format": audio_format,
    }


def display_results(results: dict):
    """Display analysis results in a well-formatted UI."""
    analysis = results["analysis"]
    answer_text = results["answer"].get("text", "")
    citations = results["citations"]
    audio_bytes = results.get("audio_bytes")
    
    # Device Information Section
    st.header("📱 Device Information")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        appliance_type = analysis.get("appliance_type") or "Unknown"
        st.metric("Appliance Type", appliance_type)
    
    with col2:
        brand_model = analysis.get("brand_or_model") or "Not identified"
        st.metric("Brand/Model", brand_model)
    
    with col3:
        part_num = analysis.get("part_number")
        part_source = analysis.get("part_number_source", "unknown")
        if part_num:
            # Show Part Number with source indicator and visual styling
            if part_source == "extracted":
                st.metric(
                    "Part Number", 
                    part_num, 
                    help="✅ Extracted directly from the image/video by analyzing visible text, labels, or nameplates"
                )
                st.caption("✅ Extracted from video/image")
            elif part_source == "predicted":
                st.metric(
                    "Part Number", 
                    part_num, 
                    help="🔮 Predicted based on appliance type. The system guessed this Part Number because it couldn't find one in the video, but this is the only Part Number available in the database for this appliance type."
                )
                st.caption("🔮 Predicted (not visible in video)")
            else:
                st.metric("Part Number", part_num)
                st.caption("Part Number identified")
        else:
            st.metric("Part Number", "Not found", delta=None)
            st.caption("⚠️ Could not extract or predict Part Number")
            st.info("💡 **Tip:** Make sure the video/image shows nameplates, labels, or documentation with part numbers clearly visible.")
    
    # Problem Analysis Section
    st.header("🔍 Problem Analysis")
    
    issue_summary = analysis.get("issue_summary") or "No issue summary available."
    st.info(f"**Issue Summary:** {issue_summary}")
    
    # Root Causes
    root_causes = analysis.get("likely_root_causes") or []
    if root_causes:
        st.subheader("Likely Root Causes")
        for i, cause in enumerate(root_causes, 1):
            st.write(f"{i}. {cause}")
    
    # Safety Warnings
    safety_warnings = analysis.get("safety_warnings") or []
    if safety_warnings:
        st.header("⚠️ Safety Warnings")
        for warning in safety_warnings:
            st.warning(warning)
    
    # Repair Instructions Section
    st.header("🔧 Repair Instructions")
    
    # Recommended fix steps from analysis
    fix_steps = analysis.get("recommended_fix_steps") or []
    if fix_steps:
        st.subheader("Recommended Steps")
        for i, step in enumerate(fix_steps, 1):
            st.write(f"**Step {i}:** {step}")
    
    # RAG-generated answer (main answer)
    if answer_text:
        st.subheader("Detailed Repair Guide")
        st.markdown(answer_text)
    
    # Tools and Parts Needed
    tools_parts = analysis.get("tools_or_parts_needed") or []
    if tools_parts:
        st.subheader("Required Tools & Parts")
        st.write(", ".join(tools_parts))
    
    # Sources and Citations
    if citations:
        st.header("📖 Sources & References")
        st.write(f"Found {len(citations)} relevant document sections:")
        
        with st.expander("View All Citations", expanded=False):
            for i, citation in enumerate(citations, 1):
                with st.container():
                    file_name = citation.get("file") or "Unknown"
                    page_num = citation.get("page")
                    snippet = citation.get("snippet", "")
                    distance = citation.get("distance")
                    
                    st.markdown(f"**Citation {i}**")
                    st.markdown(f"- **Source:** {file_name}")
                    if page_num is not None:
                        st.markdown(f"- **Page:** {page_num}")
                    if distance is not None:
                        st.markdown(f"- **Relevance Score:** {distance:.3f}")
                    if snippet:
                        st.markdown(f"- **Excerpt:** {snippet[:300]}{'...' if len(snippet) > 300 else ''}")
                    st.divider()
    
    # Follow-up Questions
    follow_ups = results.get("follow_up_questions") or []
    if follow_ups:
        st.header("❓ Follow-up Questions")
        st.write("To help diagnose the issue more accurately, consider answering these:")
        for i, question in enumerate(follow_ups[:5], 1):  # Show top 5
            st.write(f"{i}. {question}")
    
    # Transcript (expandable)
    transcript = results.get("transcript", "")
    if transcript:
        with st.expander("View Video Transcript", expanded=False):
            st.write(transcript)


def main():
    """Main Streamlit application."""
    st.markdown('<p class="main-header">🔧 Video Repair Assistant</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Upload a video or provide a URL to get AI-powered repair instructions</p>',
        unsafe_allow_html=True,
    )
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Language selector
        language = st.selectbox(
            "Response Language",
            options=["en", "ar"],
            index=0,
            help="Select the language for the AI's response",
        )
        
        # User hint input
        user_hint = st.text_area(
            "Additional Context (Optional)",
            height=100,
            help="Provide any additional context about the issue, symptoms, or questions you have",
            placeholder="E.g., 'The machine stopped working after cleaning' or 'Customer reports unusual noise'",
        )
        
        # Part number input
        part_number = st.text_input(
            "Part Number (Optional)",
            help="Enter the part number to filter results (e.g., CHS199100RECiN). If not provided, the system will try to extract it from the video.",
            placeholder="E.g., CHS199100RECiN",
        )
        
        st.divider()
        st.caption("💡 Tip: Provide context to get more accurate results")
    
    # Main content area
    tab1, tab2, tab3, tab4 = st.tabs([
        "📤 Upload Video", 
        "🖼️ Upload Image", 
        "🔗 Video URL", 
        "📚 Knowledge Base"
    ])
    
    if "last_analysis_results" not in st.session_state:
        st.session_state.last_analysis_results = None
    if "last_analysis_tab" not in st.session_state:
        st.session_state.last_analysis_tab = None
    if "last_analysis_is_image" not in st.session_state:
        st.session_state.last_analysis_is_image = None

    media_bytes = None
    mime_type = None
    is_image = False
    
    with tab1:
        st.subheader("Upload a Video File")
        uploaded_file = st.file_uploader(
            "Choose a video file",
            type=["mp4", "webm", "mov", "avi"],
            help="Supported formats: MP4, WebM, MOV, AVI. Maximum size: 25MB",
            key="video_uploader",
        )
        
        if uploaded_file is not None:
            # Read file bytes once
            media_bytes = uploaded_file.read()
            mime_type = uploaded_file.type or "video/mp4"
            is_image = False
            # Display video from bytes
            st.video(media_bytes)

        # Analyze + results only appear in Upload Video tab
        if media_bytes:
            st.divider()
            if st.button("🚀 Analyze Video", type="primary", use_container_width=True, key="analyze_media"):
                try:
                    settings = _get_settings()

                    # Validate media size
                    max_size = settings.max_video_bytes
                    if len(media_bytes) > max_size:
                        st.error(
                            f"File is too large. Maximum size: {max_size / 1024 / 1024:.0f} MB. "
                            f"Your file: {len(media_bytes) / 1024 / 1024:.2f} MB"
                        )
                    else:
                        # Process through full pipeline
                        if mime_type is None:
                            mime_type = "video/mp4" if not is_image else "image/jpeg"  # Default fallback
                        start_time = time.time()
                        results = process_video_assistance(
                            media_bytes,
                            mime_type,
                            language,
                            user_hint if user_hint.strip() else None,
                            part_number if part_number.strip() else None,
                            is_image=is_image,
                        )
                        elapsed_time = time.time() - start_time

                        st.success(f"✅ Analysis complete in {elapsed_time:.1f} seconds!")

                        # Persist results but render them only in tab1
                        st.session_state.last_analysis_results = results
                        st.session_state.last_analysis_tab = "tab1"
                        st.session_state.last_analysis_is_image = is_image

                except ValueError as e:
                    st.error(f"Configuration error: {str(e)}")
                    st.info("Please check your .env file or environment variables for GEMINI_API_KEY")
                except Exception as e:
                    error_type = type(e).__name__
                    if "VideoDownloadError" in error_type:
                        st.error(f"Video processing error: {str(e)}")
                    elif "GeminiAPIError" in error_type:
                        st.error(f"AI API error: {str(e)}")
                        if hasattr(e, 'retry_after_seconds') and e.retry_after_seconds:
                            st.info(f"Please retry after {e.retry_after_seconds} seconds")
                    else:
                        st.error(f"Unexpected error: {str(e)}")
                        st.exception(e)
        else:
            st.info("👆 Please upload a video file to begin analysis")

        # Render persisted results (only here, not in other tabs)
        if st.session_state.last_analysis_results and st.session_state.last_analysis_tab == "tab1":
            results = st.session_state.last_analysis_results
            analysis = results["analysis"]
            display_results(results)

            # ElevenLabs widget appears only after video analysis (not image)
            if not st.session_state.last_analysis_is_image:
                st.markdown("---")
                st.subheader("🎤 Voice Conversation with AI Agent")

                settings = _get_settings()
                if settings.elevenlabs_agent_id:
                    # Build runtime dynamic variable "video_context" from the Gemini analysis
                    from app.elevenlabs_agent import build_video_context_text

                    video_context = build_video_context_text(video_analysis=analysis, language=language)
                    dynamic_vars = {
                        "video_context": video_context,
                        "Customer_number": "",
                        "name": "test",
                        "phone": "test",
                        "email": "test",
                        "office_address": "test",
                        "tool_call_status": 'False',
                         "brand_or_model": analysis.get("brand_or_model") or "",
                         "appliance_type": analysis.get("appliance_type") or "",
                         "part_number": analysis.get("part_number") or "",
                    }
                    # dynamic_vars = {"video_context": video_context, 'tool_call_status': "False"}  # tool_call_status can be updated by the Agent via JS SDK when it calls tools, allowing the UI to react to tool calls in real-time if desired
                    # dynamic_vars = {"video_context": video_context, "part_number": analysis.get("part_number") or "",
                                    # "appliance_type": analysis.get("appliance_type") or "", "brand_or_model": analysis.get("brand_or_model") or ""}
                    # Escape to keep the HTML attribute safe even if transcript contains quotes/newlines.
                    dynamic_vars_attr = html.escape(
                        json.dumps(dynamic_vars, ensure_ascii=False),
                        quote=True,
                    ).replace("'", "&#39;")

                    # Optional (recommended): ensure the Agent system prompt template includes {{video_context}}
                    # This is a one-time update per Streamlit session if a write key is configured.
                    if "agent_prompt_template_updated" not in st.session_state:
                        st.session_state.agent_prompt_template_updated = False

                    api_key_write = settings.get_elevenlabs_api_key_for_write()
                    if api_key_write and not st.session_state.agent_prompt_template_updated:
                        with st.spinner("🔄 Syncing Agent prompt template (for {{video_context}})..."):
                            try:
                                from app.elevenlabs_agent import update_agent_system_instructions

                                update_agent_system_instructions(
                                    agent_id=settings.elevenlabs_agent_id,
                                    api_key=api_key_write,
                                    video_analysis=analysis,
                                    language=language,
                                )
                                st.session_state.agent_prompt_template_updated = True
                            except Exception as e:
                                logger.warning("Failed to update agent prompt template: %s", str(e))
                                st.warning(
                                    "⚠️ Couldn't sync Agent prompt template automatically. "
                                    "Make sure your Agent system prompt contains `{{video_context}}`."
                                )

                    # Embed ElevenLabs Conversational AI widget (dynamic variables injected at session start)
                    widget_html = f"""
<elevenlabs-convai
  agent-id="{settings.elevenlabs_agent_id}"
  variant="expanded"
  override-language="{language}"
  dynamic-variables='{dynamic_vars_attr}'
></elevenlabs-convai>
<script
  src="https://unpkg.com/@elevenlabs/convai-widget-embed"
  async
  type="text/javascript"
></script>
"""
                    components.html(widget_html, height=640, scrolling=True)
                else:
                    st.warning(
                        "⚠️ ELEVENLABS_AGENT_ID not configured. Please set it in .env to enable voice conversation."
                    )
                    logger.warning("ELEVENLABS_AGENT_ID not configured")
    
    with tab2:
        st.subheader("Upload an Image File")
        uploaded_image = st.file_uploader(
            "Choose an image file",
            type=["jpg", "jpeg", "png", "webp", "gif"],
            help="Supported formats: JPG, JPEG, PNG, WebP, GIF. Maximum size: 20MB",
            key="image_uploader",
        )
        
        if uploaded_image is not None:
            # Read file bytes once
            media_bytes = uploaded_image.read()
            # Determine MIME type
            if uploaded_image.type:
                mime_type = uploaded_image.type
            elif uploaded_image.name.lower().endswith(('.png',)):
                mime_type = "image/png"
            elif uploaded_image.name.lower().endswith(('.jpg', '.jpeg')):
                mime_type = "image/jpeg"
            elif uploaded_image.name.lower().endswith(('.webp',)):
                mime_type = "image/webp"
            elif uploaded_image.name.lower().endswith(('.gif',)):
                mime_type = "image/gif"
            else:
                mime_type = "image/jpeg"  # Default
            is_image = True
            # Display image
            st.image(media_bytes, use_container_width=True)
    
    with tab3:
        st.subheader("Provide Video URL")
        video_url = st.text_input(
            "Enter video URL",
            placeholder="https://example.com/video.mp4",
            help="Direct link to a video file (not YouTube or streaming services)",
        )
        
        if video_url:
            try:
                settings = _get_settings()
                with st.spinner("Downloading video..."):
                    payload = run_async(
                        _download_video(video_url, max_bytes=settings.max_video_bytes)
                    )
                    media_bytes = payload.data
                    mime_type = payload.mime_type
                    is_image = False
                    st.success(f"Video downloaded successfully ({len(media_bytes) / 1024 / 1024:.2f} MB)")
                    st.video(media_bytes)
            except Exception as e:
                error_type = type(e).__name__
                if "VideoTooLargeError" in error_type:
                    st.error(f"Video too large: {str(e)}")
                elif "VideoDownloadError" in error_type:
                    st.error(f"Failed to download video: {str(e)}")
                else:
                    st.error(f"Error downloading video: {str(e)}")
                media_bytes = None
    
    # Knowledge Base Management Tab
    with tab4:
        st.header("📚 Knowledge Base Management")
        st.markdown("**Manage documents in ElevenLabs Knowledge Base with part numbers.**")
        
        settings = _get_settings()
        
        # Import ElevenLabs functions directly (no need for FastAPI backend)
        from app.elevenlabs_knowledge_base import (
            list_documents,
            delete_document,
            upload_document_with_part_number,
            assign_knowledge_base_to_agent,
            create_or_get_folder_by_part_number,
        )
        
        if not settings.elevenlabs_api_key:
            st.error("⚠️ Missing ELEVENLABS_API_KEY. Please set it in your .env file.")
        elif not settings.elevenlabs_knowledge_base_id:
            st.warning("⚠️ Knowledge Base ID not set. Please create a Knowledge Base first.")
            
            # Create KB section
            st.subheader("Create Knowledge Base")
            kb_name = st.text_input("Knowledge Base Name", value="Technical Support Knowledge Base")
            if st.button("Create Knowledge Base"):
                with st.spinner("Creating Knowledge Base..."):
                    try:
                        from app.elevenlabs_knowledge_base import create_knowledge_base
                        result = create_knowledge_base(
                            api_key=settings.elevenlabs_api_key,
                            name=kb_name,
                        )
                        st.success(f"✅ Knowledge Base created! ID: {result['id']}")
                        st.info(f"Please add this to your .env file: ELEVENLABS_KNOWLEDGE_BASE_ID={result['id']}")
                    except Exception as e:
                        st.error(f"Error creating Knowledge Base: {str(e)}")
        else:
            st.success(f"✅ Knowledge Base ID: {settings.elevenlabs_knowledge_base_id}")
            
            # Agent Assignment Section
            st.subheader("🤖 Agent Assignment")
            col_agent1, col_agent2 = st.columns([2, 1])
            with col_agent1:
                if settings.elevenlabs_agent_id:
                    st.success(f"✅ Agent ID: {settings.elevenlabs_agent_id}")
                else:
                    st.warning("⚠️ Agent ID not set. Please set ELEVENLABS_AGENT_ID in .env")
            with col_agent2:
                if st.button("🔗 Assign KB to Agent", type="primary", use_container_width=True):
                    if not settings.elevenlabs_agent_id:
                        st.error("⚠️ Please set ELEVENLABS_AGENT_ID in .env first")
                    else:
                        with st.spinner("Assigning Knowledge Base to Agent..."):
                            try:
                                api_key = settings.get_elevenlabs_api_key_for_write()
                                result = assign_knowledge_base_to_agent(
                                    api_key=api_key,
                                    agent_id=settings.elevenlabs_agent_id,
                                    knowledge_base_id=settings.elevenlabs_knowledge_base_id,
                                )
                                status = result.get("status", "unknown")
                                
                                if status == "success":
                                    st.success("✅ Knowledge Base assigned to Agent successfully!")
                                elif status == "configured":
                                    st.info("ℹ️ Agent configuration checked. Knowledge Base should be set in Agent settings.")
                                    if result.get("note"):
                                        st.markdown(result.get("note"))
                                elif status == "manual_required":
                                    st.warning("⚠️ Manual assignment required via Dashboard")
                                    if result.get("note"):
                                        st.markdown(result.get("note"))
                                    if result.get("dashboard_url"):
                                        st.markdown(f"🔗 **Dashboard Link:** [{result.get('dashboard_url')}]({result.get('dashboard_url')})")
                                else:
                                    st.warning(f"⚠️ Assignment status: {status}")
                                    if result.get("note"):
                                        st.markdown(result.get("note"))
                            except Exception as e:
                                st.error(f"Error assigning Knowledge Base: {str(e)}")
            
            # List Documents Section
            st.subheader("📄 Documents in Knowledge Base")
            
            # Folder filter
            col_filter1, col_filter2 = st.columns(2)
            with col_filter1:
                folder_name = st.text_input(
                    "📁 Folder Name (optional)",
                    value="",
                    help="Enter folder name (e.g., 'sm') to list documents from that folder only",
                    placeholder="e.g., sm"
                )
            with col_filter2:
                parent_folder_id = st.text_input(
                    "📁 Folder ID (optional)",
                    value="",
                    help="Or enter folder ID directly",
                    placeholder="folder_id_here"
                )
            
            if st.button("🔄 Refresh Documents List", type="secondary"):
                with st.spinner("Loading documents..."):
                    try:
                        api_key = settings.get_elevenlabs_api_key_for_read()
                        documents = list_documents(
                            api_key=api_key,
                            knowledge_base_id=settings.elevenlabs_knowledge_base_id,
                            parent_folder_id=parent_folder_id if parent_folder_id else None,
                            folder_name=folder_name if folder_name else None,
                        )
                        st.session_state.kb_documents = documents
                        st.success(f"✅ Loaded {len(documents)} documents")
                    except Exception as e:
                        st.error(f"Error loading documents: {str(e)}")
            
            # Display documents
            if "kb_documents" in st.session_state and st.session_state.kb_documents:
                st.write(f"**Total Documents:** {len(st.session_state.kb_documents)}")
                
                for doc in st.session_state.kb_documents:
                    with st.container():
                        col1, col2, col3 = st.columns([3, 1, 1])
                        with col1:
                            st.markdown(f"**{doc.get('name', 'Unknown')}**")
                            if doc.get('part_number'):
                                st.caption(f"Part Number: {doc['part_number']}")
                        with col2:
                            st.caption(f"ID: {doc.get('document_id', '')[:8]}...")
                        with col3:
                            if st.button("🗑️ Delete", key=f"delete_{doc.get('document_id')}", type="secondary"):
                                with st.spinner("Deleting document..."):
                                    try:
                                        api_key = settings.get_elevenlabs_api_key_for_write()
                                        delete_document(
                                            api_key=api_key,
                                            knowledge_base_id=settings.elevenlabs_knowledge_base_id,
                                            document_id=doc.get('document_id'),
                                        )
                                        st.success("✅ Document deleted")
                                        # Refresh list
                                        if "kb_documents" in st.session_state:
                                            st.session_state.kb_documents = [
                                                d for d in st.session_state.kb_documents
                                                if d.get('document_id') != doc.get('document_id')
                                            ]
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error deleting document: {str(e)}")
                        st.divider()
            
            # Upload New Document Section
            st.subheader("📤 Upload Documents")
            
            uploaded_docs = st.file_uploader(
                "Choose document files (you can select multiple files)",
                type=["pdf", "txt", "docx", "md"],
                accept_multiple_files=True,
                help="Upload one or more documents to add to the Knowledge Base. All files will be uploaded to the same folder based on part number.",
            )
            
            col_upload1, col_upload2 = st.columns([2, 1])
            with col_upload1:
                doc_part_number = st.text_input(
                    "Part Number",
                    placeholder="E.g., CHS199100RECiN",
                    help="Enter the part number for all documents. All files will be organized in folder: Part_{part_number}",
                )
            with col_upload2:
                doc_custom_names = st.text_input(
                    "Custom Names (Optional)",
                    placeholder="Manual_1, Manual_2, Manual_3",
                    help="Optional comma-separated custom names (must match number of files)",
                )
            
            # Display uploaded files
            if uploaded_docs:
                st.write(f"**Selected Files ({len(uploaded_docs)}):**")
                for i, doc in enumerate(uploaded_docs, 1):
                    file_size = len(doc.read()) / 1024 / 1024  # Size in MB
                    doc.seek(0)  # Reset file pointer
                    st.caption(f"{i}. {doc.name} ({file_size:.2f} MB)")
            
            # Upload button
            upload_button_text = "📤 Upload All Documents" if uploaded_docs and len(uploaded_docs) > 1 else "📤 Upload Document"
            if st.button(upload_button_text, type="primary", use_container_width=True):
                if not uploaded_docs or len(uploaded_docs) == 0:
                    st.error("⚠️ Please select at least one file to upload")
                elif not doc_part_number:
                    st.error("⚠️ Please enter a part number")
                else:
                    # Validate custom names if provided
                    custom_names_list = None
                    if doc_custom_names:
                        custom_names_list = [name.strip() for name in doc_custom_names.split(",")]
                        if len(custom_names_list) != len(uploaded_docs):
                            st.error(f"⚠️ Number of custom names ({len(custom_names_list)}) must match number of files ({len(uploaded_docs)})")
                            st.stop()
                    
                    # Upload with progress
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    try:
                        api_key = settings.get_elevenlabs_api_key_for_write()
                        kb_id = settings.elevenlabs_knowledge_base_id
                        
                        # Create or get folder for this part number
                        status_text.text("Creating folder...")
                        folder_id = create_or_get_folder_by_part_number(api_key, doc_part_number)
                        progress_bar.progress(0.1)
                        
                        # Upload all files
                        results = []
                        failed_uploads = []
                        total_files = len(uploaded_docs)
                        
                        for idx, doc in enumerate(uploaded_docs):
                            try:
                                status_text.text(f"Uploading {doc.name}... ({idx + 1}/{total_files})")
                                doc.seek(0)
                                file_bytes = doc.read()
                                mime_type = doc.type
                                custom_name = custom_names_list[idx] if custom_names_list else None
                                
                                result = upload_document_with_part_number(
                                    file_bytes=file_bytes,
                                    file_name=doc.name,
                                    part_number=doc_part_number,
                                    api_key=api_key,
                                    knowledge_base_id=kb_id,
                                    custom_name=custom_name,
                                    mime_type=mime_type,
                                    parent_folder_id=folder_id,
                                )
                                
                                results.append({
                                    "file_name": doc.name,
                                    "document_id": result["document_id"],
                                    "name": result["name"],
                                })
                                
                                progress_bar.progress(0.1 + (0.8 * (idx + 1) / total_files))
                                
                            except Exception as e:
                                failed_uploads.append({
                                    "file_name": doc.name,
                                    "error": str(e),
                                })
                        
                        progress_bar.progress(1.0)
                        status_text.empty()
                        
                        # Display results
                        successful = len(results)
                        failed = len(failed_uploads)
                        
                        if successful > 0:
                            st.success(f"✅ Successfully uploaded {successful}/{total_files} document(s)!")
                            
                            if folder_id:
                                st.info(f"📁 Folder: Part_{doc_part_number} (ID: {folder_id})")
                            
                            with st.expander(f"✅ Successful Uploads ({successful})", expanded=True):
                                for upload_result in results:
                                    st.markdown(f"**{upload_result.get('file_name')}**")
                                    st.caption(f"Document ID: {upload_result.get('document_id')}")
                                    st.caption(f"Name: {upload_result.get('name')}")
                                    st.divider()
                        
                        if failed > 0:
                            with st.expander(f"❌ Failed Uploads ({failed})", expanded=False):
                                for failed_upload in failed_uploads:
                                    st.error(f"**{failed_upload.get('file_name')}**")
                                    st.caption(f"Error: {failed_upload.get('error')}")
                                    st.divider()
                        
                        # Refresh documents list
                        if "kb_documents" in st.session_state:
                            del st.session_state.kb_documents
                            
                    except Exception as e:
                        progress_bar.empty()
                        status_text.empty()
                        st.error(f"Error uploading documents: {str(e)}")
                        st.exception(e)
    
    # Footer
    st.divider()
    # st.caption("Powered by Gemini AI • Built with Streamlit • RAG-powered repair assistance")


if __name__ == "__main__":
    main()

