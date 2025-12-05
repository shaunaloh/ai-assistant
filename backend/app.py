import os
import sys
import traceback

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from sqlalchemy.orm import Session
from google import genai
from dotenv import load_dotenv

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import Base, engine, SessionLocal
from backend.models import ChatMessage

# Load environment variables from .env file
load_dotenv()

# Initialize the Google Generative AI client with the API key
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

app = Flask(__name__, template_folder="../frontend", static_folder="../frontend/static")
# Enable CORS for all routes
CORS(app)

# Create DB if needed
Base.metadata.create_all(bind=engine)

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

        # Call LLM using Google Generative AI
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        # Parse the response
        bot_output = response.text if response.text else "No response from model"

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
