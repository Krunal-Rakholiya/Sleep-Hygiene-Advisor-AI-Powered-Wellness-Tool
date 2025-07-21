from flask import Flask, render_template, request, jsonify, redirect, url_for
import google.generativeai as genai
from dotenv import load_dotenv
import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configure Gemini API using the key from the environment
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///advice_history.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class AdviceHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    answers = db.Column(db.Text)  # Store as stringified list
    advice = db.Column(db.Text)

with app.app_context():
    db.create_all()

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    # Accept JSON data from chatbot
    if request.is_json:
        data = request.get_json()
        answers = data.get("answers", [])
        # Map answers to questions
        sleep_duration = answers[0] if len(answers) > 0 else ""
        bedtime = answers[1] if len(answers) > 1 else ""
        wake_time = answers[2] if len(answers) > 2 else ""
        screen_time = answers[3] if len(answers) > 3 else ""
        caffeine = answers[4] if len(answers) > 4 else ""
        activity = answers[5] if len(answers) > 5 else ""
        issues = answers[6] if len(answers) > 6 else "None"

        prompt = f"""
Act as a friendly wellness coach. Based on the following sleep habits, give practical and supportive advice to help me improve my sleep hygiene. Please be positive, motivational, and avoid any complex medical terms.

Sleep Summary:
- I sleep {sleep_duration} hours.
- Bedtime: {bedtime}, Wake-up: {wake_time}.
- Screen time before bed: {screen_time}.
- Caffeine after 6 PM: {caffeine}.
- Physical activity: {activity}.
- Issues: {issues if issues else 'none'}

Format your response in 3 sections:
1. What's going well 🌟
2. What needs improvement 🔧
3. Personalized advice 📋
.
"""
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        advice = response.text
        # Save to database
        history = AdviceHistory(answers=str(answers), advice=advice)
        db.session.add(history)
        db.session.commit()
        return jsonify({"advice": advice})
    else:
        return jsonify({"error": "Invalid request"}), 400

@app.route("/history", methods=["GET"])
def history():
    all_history = AdviceHistory.query.order_by(AdviceHistory.timestamp.desc()).all()
    return render_template("history.html", history=all_history)

if __name__ == "__main__":
    app.run(debug=True)



