# Fauxy Chatbot

A satirical news chatbot that takes real news and adds a humorous twist, Indian-style! 🇮🇳

## Quick Start

1. Clone the repo
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Choose your version:

### Local Version (app.py)
- Uses Ollama for local model inference
- Runs everything on your machine
- Better privacy, no API costs
```bash
python app.py
```

### Cloud Version (newapp.py)
- Uses GROQ's API for faster responses
- Requires API keys (see below)
- Better performance, no local GPU needed
```bash
# Set up your .env file first!
python newapp.py
```

## API Keys Needed

For both versions:
- `NEWS_API_KEY` from NewsAPI.org

Additional for cloud version:
- `GROQ_API_KEY` from groq.com

## Dependencies

Main requirements:
- Flask
- Requests
- Transformers (local version)
- python-dotenv (cloud version)

See `requirements.txt` for the full list.

## Models

Local version needs:
- Ollama installed
- Our custom model loaded (see Modelfile)

Cloud version uses GROQ's hosted models (no setup needed).

---

Love India - Fauxy!
