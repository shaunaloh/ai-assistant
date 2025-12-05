import os
import sys
import traceback
import requests

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from sqlalchemy.orm import Session
from google import genai
from dotenv import load_dotenv

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import Base, engine, SessionLocal
from backend.models import ChatMessage
from backend.agents import llm_router, singstat_agent, datagov_agent

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

        # Use the LLM router to determine which agent to use
        agent = llm_router(prompt)
        if agent == "singstat":
            bot_output = singstat_agent(prompt)
        elif agent == "datagov":
            bot_output = datagov_agent(prompt)
        else:
            # fallback to LLM if agent is unknown
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
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

@app.post("/weather")
def weather():
    try:
        # Fetch weather forecast from Data.gov.sg
        datagov_api_url = "https://api.data.gov.sg/v1/environment/24-hour-weather-forecast"
        response = requests.get(datagov_api_url)
        if response.status_code == 200:
            data = response.json()
            forecast = data.get("items", [{}])[0].get("general", {}).get("forecast", "No forecast available")
            return jsonify({"forecast": forecast})
        else:
            return jsonify({"error": f"Failed to fetch data from Data.gov.sg. Status code: {response.status_code}"}), 500
    except Exception as e:
            return jsonify({"error": f"An error occurred while fetching data: {str(e)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)