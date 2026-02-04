from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

app = Flask(__name__)
CORS(app)  # allow all origins for simplicity

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.1-8b-instant"


# -------------------------
# 1. GENERATE PLAN (bigGoal + sampleMountain + sampleDailyStep)
# -------------------------
@app.route("/generate-plan", methods=["POST"])
def generate_plan():
    data = request.json
    vague_goal = data.get("vagueGoal")
    clarifications = data.get("clarifications", [])

    system_prompt = (
        "You are the Swiss Chocolate Coach. Convert vague goals into a clear big goal, "
        "then create ONE sample weekly mountain and ONE sample daily step.\n\n"
        "Respond ONLY in JSON with keys:\n"
        "bigGoal: string,\n"
        "weeklyMountain: { name, weeklyTarget, note },\n"
        "dailyStep: string\n"
        "IMPORTANT: weeklyMountain must NOT include a tasks list. Keep it simple."
    )

    user_prompt = f"Vague Goal: {vague_goal}\n\nUser Clarifications:\n- " + "\n- ".join(clarifications)

    payload = {
        "model": MODEL,
        "temperature": 0.7,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }

    groq_res = requests.post(GROQ_URL, headers=headers, json=payload)
    try:
        content = groq_res.json()["choices"][0]["message"]["content"]
        return jsonify({"success": True, "data": content})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# -------------------------
# 2. WEEKLY MOUNTAIN GENERATOR (real production)
# -------------------------
@app.route("/generate-weekly-mountain", methods=["POST"])
def generate_weekly_mountain():
    data = request.json
    big_goal = data.get("bigGoal")

    system_prompt = (
        "Generate the FIRST weekly mountain for the user's big goal.\n"
        "Respond ONLY in JSON with keys: name, weeklyTarget, tasks (5-7 strings), note."
    )

    user_prompt = f"Big goal: {big_goal}"

    payload = {
        "model": MODEL,
        "temperature": 0.7,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }

    groq_res = requests.post(GROQ_URL, headers=headers, json=payload)
    try:
        content = groq_res.json()["choices"][0]["message"]["content"]
        return jsonify({"success": True, "data": content})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# -------------------------
# 3. DAILY SWEETSTEPS
# -------------------------
@app.route("/generate-daily-steps", methods=["POST"])
def generate_daily_steps():
    data = request.json
    big_goal = data.get("bigGoal")

    system_prompt = (
        "Generate today's micro-steps for the user's big goal. "
        "Respond ONLY in JSON with keys: steps (3-6 items), coachNote (string). "
        "Tone warm, friendly, calm."
    )

    user_prompt = f"Generate actionable daily micro-steps for this goal: {big_goal}"

    payload = {
        "model": MODEL,
        "temperature": 0.7,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }

    groq_res = requests.post(GROQ_URL, headers=headers, json=payload)
    try:
        content = groq_res.json()["choices"][0]["message"]["content"]
        return jsonify({"success": True, "data": content})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# -------------------------
# RUN LOCAL
# -------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)