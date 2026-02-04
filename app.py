from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq
import json
import os

app = Flask(__name__)

# Minimal, safe, Caffeine-compatible CORS
CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    methods=["GET", "POST", "OPTIONS"]
)

@app.route("/<path:path>", methods=["OPTIONS"])
def options_handler(path):
    return ("", 204)


# --------------------------------------------
# GROQ CLIENT
# --------------------------------------------
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# --------------------------------------------
# SAFE JSON PARSER FOR RENDER
# --------------------------------------------
def get_json():
    try:
        if request.is_json:
            return request.get_json()
        raw = request.data.decode("utf-8")
        print("RAW BODY FROM RENDER:", raw)
        return json.loads(raw) if raw else {}
    except Exception as e:
        print("JSON PARSE ERROR:", e)
        return {}


# ===================================================================
# 1) ONBOARDING PLAN  (matches goldfish EXACTLY)
# ===================================================================
@app.post("/onboarding-plan")
def onboarding_plan():
    data = get_json()

    vague_goal = data.get("vagueGoal")
    progress = data.get("currentProgress")
    time_limit = data.get("timeLimit")

    if not vague_goal or not progress or not time_limit:
        print("BAD BODY RECEIVED:", data)
        return jsonify({
            "error": "vagueGoal, currentProgress, and timeLimit are required"
        }), 400

    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        temperature=0.7,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "Generate a big goal, weekly mountain info, and daily sample step. "
                    "Return strict JSON: "
                    "{ bigGoal, weeklyMountain { name, weeklyTarget, note }, dailyStep }"
                )
            },
            {
                "role": "user",
                "content": (
                    f"Vague Goal: {vague_goal}\n"
                    f"Current Progress: {progress}\n"
                    f"Time Limit: {time_limit}"
                )
            }
        ]
    )

    return jsonify(json.loads(completion.choices[0].message.content))


# ===================================================================
# 2) WEEKLY MOUNTAIN  (matches goldfish EXACTLY)
# ===================================================================
@app.post("/weekly-mountain")
def weekly_mountain():
    data = get_json()
    big_goal = data.get("bigGoal")

    if not big_goal:
        print("BAD BODY RECEIVED:", data)
        return jsonify({"error": "bigGoal required"}), 400

    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        temperature=0.7,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": "Return strict JSON: { name, weeklyTarget, note }"
            },
            {
                "role": "user",
                "content": f"Big Goal: {big_goal}"
            }
        ]
    )

    return jsonify(json.loads(completion.choices[0].message.content))


# ===================================================================
# 3) DAILY SWEETSTEPS  (matches goldfish EXACTLY)
# ===================================================================
@app.post("/daily-steps")
def daily_steps():
    data = get_json()

    big_goal = data.get("bigGoal")
    weekly_mountain = data.get("weeklyMountain")  # object

    if not big_goal or not weekly_mountain:
        print("BAD BODY RECEIVED:", data)
        return jsonify({"error": "bigGoal and weeklyMountain required"}), 400

    def ask_groq():
        try:
            c = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                temperature=0.7,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Generate today's daily SweetSteps using BOTH the big goal "
                            "and weekly mountain.\n"
                            "Return JSON: { steps: [ {title, description, minutes} ], coachNote }"
                        )
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Big Goal: {big_goal}\n"
                            f"Weekly Mountain: {weekly_mountain}"
                        )
                    }
                ]
            )
            return json.loads(c.choices[0].message.content)
        except Exception as e:
            print("Groq JSON error:", e)
            return None

    result = ask_groq()
    if result is None:
        print("Retrying Groq…")
        result = ask_groq()

    if result is None:
        return jsonify({
            "error": "Groq returned invalid JSON twice",
            "fallback": {
                "steps": [
                    {"title": "Warm up", "description": "Start small", "minutes": 5},
                    {"title": "Main push", "description": "Move goal forward", "minutes": 15},
                ],
                "coachNote": "Fallback activated; keep pushing!"
            }
        }), 500

    return jsonify(result)


# ===================================================================
# 4) HEALTH CHECK
# ===================================================================
@app.get("/")
def health():
    return {"status": "alive"}, 200