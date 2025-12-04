from flask import Flask, render_template, request
from sqlalchemy.orm import Session
import sys
import os

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import Base, engine, SessionLocal
from backend.models import ChatMessage
import requests

app = Flask(__name__, template_folder="../frontend", static_folder="../frontend/static")

# Create DB if needed
Base.metadata.create_all(bind=engine)

OLLAMA_URL = "http://host.docker.internal:11434/api/generate"  
MODEL = "llama3.2"

@app.get("/")
def index():
    db = SessionLocal()
    messages = db.query(ChatMessage).all()
    return render_template("index.html", messages=messages, error=None)

@app.post("/chat")
def chat():
    prompt = request.form.get("prompt")
    if not prompt:
        return render_template("index.html", messages=[], error="Prompt is required.")

    # Call LLM via Ollama
    try:
        payload = {"model": MODEL, "prompt": prompt}
        response = requests.post(OLLAMA_URL, json=payload)

        bot_output = response.json()["response"]

    except Exception as e:
        return render_template("index.html", messages=[], error=f"LLM error: {e}")

    # Save to DB
    db = SessionLocal()
    msg = ChatMessage(user_input=prompt, bot_response=bot_output)
    db.add(msg)
    db.commit()

    messages = db.query(ChatMessage).all()
    return render_template("index.html", messages=messages, error=None)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
