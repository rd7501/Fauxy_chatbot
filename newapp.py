# Cloud API Version
from flask import Flask, request, jsonify
import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

# --- CONFIG: use environment variables instead of hardcoding secrets ---
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # <-- set this in .env or env
# Recommendation: replace with a supported model if you previously used llama3-70b-8192
GROQ_MODEL_NAME = os.getenv("GROQ_MODEL_NAME", "llama-3.3-70b-versatile")

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODELS_URL = "https://api.groq.com/openai/v1/models"  # list models programmatically

if not GROQ_API_KEY:
    raise RuntimeError("Please set GROQ_API_KEY in your environment or .env file (do NOT keep it in source).")

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False


def call_groq(payload):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    print(">>> GROQ Request JSON:", json.dumps(payload, indent=2, ensure_ascii=False))
    resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=60)
    print("<<< GROQ status:", resp.status_code)
    if resp.status_code != 200:
        print("<<< GROQ response text:", resp.text)
    # Let caller handle errors
    return resp


@app.route('/models', methods=['GET'])
def list_models():
    """Return the list of available models for your GROQ key (useful to pick a valid model)."""
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    try:
        r = requests.get(GROQ_MODELS_URL, headers=headers, timeout=20)
        r.raise_for_status()
        return jsonify(r.json())
    except Exception as e:
        print("Error listing models:", e)
        return jsonify({"error": "Could not list models", "details": str(e)}), 500


@app.route('/satire', methods=['POST'])
def generate_satire():
    data = request.get_json(force=True, silent=True)
    if not data or "topic" not in data:
        return jsonify({"error": "Please provide JSON with a 'topic' field."}), 400

    topic = data["topic"]
    print(f"Received topic: {topic}")

    # Fetch news
    try:
        news_url = f"https://newsapi.org/v2/everything?q={topic}&language=en&pageSize=1&apiKey={NEWS_API_KEY}"
        r = requests.get(news_url, timeout=10)
        r.raise_for_status()
        news_json = r.json()
        if not news_json.get("articles"):
            return jsonify({"error": f"No articles found for '{topic}'"}), 404
        article = news_json["articles"][0]
        factual_content = article.get("description") or article.get("title") or "No description available."
    except Exception as e:
        print("News fetch error:", e)
        return jsonify({"error": f"Failed to fetch news: {e}"}), 500

    final_prompt = f"""
You are a news correspondent for 'The Fauxy', India's top satirical news source.
Your tone is witty, sarcastic, and darkly humorous. Keep your report short (under 1 paragraph).
Each paragraph should be concise, punchy, and comedic. End with a clever line or fake quote.
REAL NEWS: {factual_content}
Now, your satirical version:
"""

    groq_payload = {
        "model": GROQ_MODEL_NAME,
        "messages": [
            {"role": "system", "content": "You are 'The Fauxy' satire writer with sharp wit."},
            {"role": "user", "content": final_prompt}
        ],
        "temperature": 0.8,
        "max_tokens": 250
    }

    # Ensure correct types
    groq_payload["max_tokens"] = int(groq_payload.get("max_tokens", 400))
    groq_payload["temperature"] = float(groq_payload.get("temperature", 0.8))

    try:
        resp = call_groq(groq_payload)
        # If GROQ returns an HTTP error we want to handle it gracefully:
        if resp.status_code == 400:
            # try to decode JSON error
            try:
                err = resp.json()
                # If the model was decommissioned, GROQ returns code "model_decommissioned"
                code = err.get("error", {}).get("code", "")
                msg = err.get("error", {}).get("message", "")
                if code == "model_decommissioned" or "decommissioned" in msg.lower():
                    # Helpful error to user + pointer to GROQ docs
                    suggestion = {
                        "error": "model_decommissioned",
                        "message": msg,
                        "suggested_action": (
                            "Pick a supported model (e.g. 'llama-3.3-70b-versatile' or 'llama-3.1-8b-instant') "
                            "or list available models via GET /models endpoint. See GROQ deprecations: "
                            "https://console.groq.com/docs/deprecations"
                        )
                    }
                    print("Model decommissioned — provider message:", msg)
                    return jsonify(suggestion), 400
                # otherwise return the raw provider error
                return jsonify({"error": "GROQ returned 400", "details": err}), 400
            except ValueError:
                # Not JSON — return raw text
                return jsonify({"error": "GROQ returned 400", "details": resp.text}), 400

        resp.raise_for_status()  # raise for other non-200 statuses
        groq_json = resp.json()
        choices = groq_json.get("choices", [])
        if not choices:
            return jsonify({"error": "GROQ returned no choices", "raw": groq_json}), 500
        assistant_msg = choices[0].get("message", {}).get("content") or choices[0].get("text", "")
        return jsonify({"topic": topic, "satire": assistant_msg.strip()})
    except requests.exceptions.HTTPError as e:
        print("HTTP error calling GROQ:", e)
        return jsonify({"error": "GROQ HTTP error", "details": str(e)}), 502
    except Exception as e:
        print("Unexpected error:", e)
        return jsonify({"error": f"Unexpected error: {e}"}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
