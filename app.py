# app.py (Using NewsAPI.org for descriptions)
from flask import Flask, request, jsonify
import requests
import json
# Removed xml.etree.ElementTree as we are using JSON now
import os

# --- Configuration ---
NEWS_API_KEY = "NEWS_API_KEY" # Your NewsAPI.org key
OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL_NAME = "fauxybot"


# --- Initialize Flask App ---
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False


# --- Main Chatbot Function ---
@app.route('/satire', methods=['POST'])
def generate_satire():
    data = request.get_json()
    if not data or 'topic' not in data:
        return jsonify({"error": "No topic provided"}), 400
    
    topic = data['topic']
    print(f"🔄 Received topic: {topic}")

    # 1. Fetch factual news summary from NewsAPI.org
    try:
        # --- MODIFIED: Using NewsAPI.org endpoint ---
        news_url = f"https://newsapi.org/v2/everything?q={topic}&language=en&pageSize=1&apiKey={NEWS_API_KEY}"
        response = requests.get(news_url, timeout=10)
        response.raise_for_status()
        news_data = response.json() # NewsAPI returns JSON
        
        if not news_data.get('articles'):
            return jsonify({"error": f"Could not find any news articles for '{topic}' via NewsAPI.org"}), 404
            
        # --- MODIFIED: Get the description (summary) instead of just title ---
        # Use description if available, otherwise fall back to title
        article = news_data['articles'][0]
        factual_content = article.get('description') or article.get('title') 
        if not factual_content: # Handle cases where both might be missing/empty
             return jsonify({"error": "Found article but it has no description or title."}), 404
        # --- END OF MODIFICATIONS ---

        print(f"📰 Found news summary: {factual_content}")
        
    except requests.exceptions.RequestException as e:
        print(f"Error during news fetch: {e}")
        return jsonify({"error": f"Failed to fetch news from NewsAPI.org: {e}"}), 500
    except Exception as e: # Catch other potential errors like JSON parsing
        print(f"Error processing news data: {e}")
        return jsonify({"error": f"Failed processing news data: {e}"}), 500


    # 2. Construct the final, personality-driven prompt
    final_prompt_text = f"""You are a news correspondent for 'The Fauxy', India's premier satirical news source. Your tone is witty, extremely sarcastic, and satirical. Your job is to read a real news summary and provide the real, darkly humorous, and ironic story behind the story. Use a mix of sharp English and common Indian slang or phrases where it feels natural. Be cynical, find the absurdity, and be satirically optimistic. Answer everything sarcastically.

Here is today's boring, official news summary:
REAL NEWS: {factual_content}

Now, here is your Fauxy report:
THE FAUXY REPORT:"""
    
    # 3. Send the prompt to our local Ollama model
    try:
        ollama_payload = {
            "model": OLLAMA_MODEL_NAME,
            "prompt": final_prompt_text,
            "stream": False,
            "options": {
                "temperature": 0.8
            }
        }
        
        print(f"🤖 Asking '{OLLAMA_MODEL_NAME}' for a response...")
        response = requests.post(OLLAMA_API_URL, json=ollama_payload)
        response.raise_for_status()
        
        full_response = response.json()
        satirical_article = full_response.get("response", "No content generated.")

        print("✅ Generated satire successfully.")
        return jsonify({"topic": topic, "satire": satirical_article.strip()})
        
    except requests.exceptions.RequestException as e:
        print(f"Error during Ollama communication: {e}")
        return jsonify({"error": f"Failed to communicate with Ollama model: {e}"}), 500


# --- Run the App ---
if __name__ == '__main__':
    # Use host='0.0.0.0' to make it accessible on your network if needed
    app.run(debug=True, port=5000)
