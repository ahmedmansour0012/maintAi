# MaintAI — Video Repair Assistant

Streamlit app that analyzes appliance videos/images with Gemini AI and delivers repair instructions via ElevenLabs voice and text agents.

> **Backend API (subcontractor & appointment lookup):** see [Api/README.md](Api/README.md)

---

## Setup

```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install "elevenlabs[pyaudio]"
```

Copy `env.example` to `.env` and fill in all keys:

| Key | Description |
|---|---|
| `GEMINI_API_KEY` | Google Gemini API key |
| `ELEVENLABS_API_KEY` | ElevenLabs read key |
| `ELEVENLABS_API_KEY_WRITE` | ElevenLabs write key |
| `ELEVENLABS_AGENT_ID` | Voice agent ID |
| `ELEVENLABS_TXT_AGENT_ID` | Text agent ID |
| `ELEVENLABS_KNOWLEDGE_BASE_ID` | Knowledge base ID |

```cmd
streamlit run streamlit_app.py
```

Opens at `http://localhost:8501`. For a public URL use ngrok: `ngrok http 8501`

---

## Features

| Tab | Description |
|---|---|
| Upload Video | Analyze video → repair guide + voice widget |
| Upload Image | Analyze image → repair guide |
| Video URL | Download from URL → analyze |
| Knowledge Base | Manage ElevenLabs KB documents |

Sidebar: language (EN/AR), context hint, part number filter.
