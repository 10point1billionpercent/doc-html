from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

app = Flask(__name__)
CORS(app)

# --------------------------------------------------
# Helper: Call Groq
# --------------------------------------------------
def call_groq(system_prompt, user_prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }

    body = {
        "model": "llama-3.1-8b-instant",
        "temperature": 0.7,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }

    response = requests.post(url, json=body, headers=headers)

    if response.status_code != 200:
        print("Groq error:", response.text)
        return None

    try:
        content = response.json()['choices'][0]['message']['content']
        return json.loads(content)
    except Exception as e:
        print("JSON parse error:", e)
        return None


# --------------------------------------------------
# 1. Onboarding endpoint
# --------------------------------------------------
@app.post("/onboarding-plan")
def onboarding_plan():
    data = request.json
    vague = data.get("vagueGoal", "")
    clar = data.get("clarifications", [])

    system_prompt = (
        "You are the Swiss Chocolate Coach. Convert a vague goal into a clear big goal, "
        "create ONE sample weekly mountain, and ONE sample daily SweetStep. "
        "Respond ONLY in JSON with:\n"
        "{ bigGoal, weeklyMountain: { name, weeklyTarget, note }, dailyStep }"
    )

    user_prompt = (
        f"Vague goal: {vague}\n"
        f"Clarifications:\n- " + "\n- ".join(clar)
    )

    result = call_groq(system_prompt, user_prompt)
    return jsonify(result or {})


# --------------------------------------------------
# 2. Weekly Mountain endpoint
# --------------------------------------------------
@app.post("/weekly-mountain")
def weekly_mountain():
    data = request.json
    big = data.get("bigGoal", "")

    system_prompt = (
        "Generate a single weekly mountain for the user's big goal. "
        "Respond ONLY in JSON:\n"
        "{ name, weeklyTarget, note }"
    )

    user_prompt = f"Big goal: {big}"

    result = call_groq(system_prompt, user_prompt)
    return jsonify(result or {})


# --------------------------------------------------
# 3. DAILY SWEETSTEPS endpoint (UPDATED)
# --------------------------------------------------
@app.post("/daily-steps")
def daily_steps():
    data = request.json

    big = data.get("bigGoal", "")
    weekly = data.get("weeklyMountain", {})

    system_prompt = (
        "Generate today's micro-steps based on BOTH the user's big goal AND their "
        "current weekly mountain. Respond ONLY in JSON with the key:\n"
        "{ steps: [ { task: string, time: number_in_minutes } ] }\n"
        "Generate 3–6 realistic microtasks. Time must be an integer (5, 10, 15, 20)."
    )

    user_prompt = (
        f"Big goal: {big}\n\n"
        f"Weekly mountain:\n"
        f"- Name: {weekly.get('name')}\n"
        f"- Weekly target: {weekly.get('weeklyTarget')}\n"
        f"- Tasks: {weekly.get('tasks')}\n"
        f"- Note: {weekly.get('note')}"
    )

    result = call_groq(system_prompt, user_prompt)
    return jsonify(result or {})


# --------------------------------------------------
# Main
# --------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)