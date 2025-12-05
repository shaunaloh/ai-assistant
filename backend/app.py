from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from sqlalchemy.orm import Session
import sys
import os
import traceback
import time

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import Base, engine, SessionLocal
from backend.models import ChatMessage
import requests

app = Flask(__name__, template_folder="../frontend", static_folder="../frontend/static")
# Enable CORS for all routes
CORS(app)

# Create DB if needed
Base.metadata.create_all(bind=engine)

# Ollama URL: local by default, or set OLLAMA_URL env var for remote Ollama/LLM endpoint
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
# Default model - configurable via env var if you want a faster model
MODEL = os.environ.get("AI_MODEL", "llama3.2")
# Limit tokens to keep responses snappy; adjust via env `AI_MAX_TOKENS`
DEFAULT_MAX_TOKENS = int(os.environ.get("AI_MAX_TOKENS", "250"))

@app.get("/")
def index():
    try:
        db = SessionLocal()
        messages = db.query(ChatMessage).all()
        db.close()
        return render_template("index.html", messages=messages, error=None)
    except Exception as e:
        print(f"Error in index: {e}")
        traceback.print_exc()
        return render_template("index.html", messages=[], error=str(e))

@app.post("/chat")
def chat():
    db = SessionLocal()
    try:
        prompt = request.form.get("prompt")
        print(f"Received prompt: {prompt}")

        if not prompt:
            messages = db.query(ChatMessage).all()
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"messages": [
                    {"user_input": m.user_input, "bot_response": m.bot_response} for m in messages
                ], "error": "Prompt is required."})
            return render_template("index.html", messages=messages, error="Prompt is required.")

        # Call LLM via Ollama (measure time)
        try:
            payload = {"model": MODEL, "prompt": prompt, "stream": False, "max_tokens": DEFAULT_MAX_TOKENS}
            start = time.time()
            response = requests.post(OLLAMA_URL, json=payload, timeout=120)
            wall_time = time.time() - start
            print(f"Ollama response status: {response.status_code}, wall_time: {wall_time:.2f}s")

            try:
                elapsed = getattr(response.elapsed, "total_seconds", lambda: None)()
            except Exception:
                elapsed = None
            print(f"requests.elapsed: {elapsed}")

            bot_output = response.json().get("response")

        except Exception as e:
            print(f"Error calling Ollama: {e}")
            traceback.print_exc()
            messages = db.query(ChatMessage).all()
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"messages": [
                    {"user_input": m.user_input, "bot_response": m.bot_response} for m in messages
                ], "error": f"LLM error: {e}"})
            return render_template("index.html", messages=messages, error=f"LLM error: {e}")

        # Save to DB
        msg = ChatMessage(user_input=prompt, bot_response=bot_output)
        db.add(msg)
        db.commit()
        print(f"Message saved to DB with id: {msg.id}")

        messages = db.query(ChatMessage).all()

        # If AJAX request, return JSON for faster frontend updates
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({
                "messages": [
                    {"user_input": m.user_input, "bot_response": m.bot_response} for m in messages
                ],
                "error": None,
            })

        return render_template("index.html", messages=messages, error=None)
    except Exception as e:
        print(f"Error in chat: {e}")
        traceback.print_exc()
        messages = db.query(ChatMessage).all()
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"messages": [
                {"user_input": m.user_input, "bot_response": m.bot_response} for m in messages
            ], "error": f"Server error: {e}"})
        return render_template("index.html", messages=messages, error=f"Server error: {e}")
    finally:
        db.close()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
