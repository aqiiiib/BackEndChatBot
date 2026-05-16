# This file represents the "Natural Language Interface" and "Server" tier
# of the 3-tier architecture. It handles user input (HTTP requests) and passes
# it to the Inference Engine for processing.
from flask import Flask, request, jsonify
from flask_cors import CORS
from knowledge_base import (
    init_db,
    add_learned_response,
    get_unanswered_queries,
    get_all_packages,
)
from inference_engine import get_response

app = Flask(__name__)
CORS(app)

@app.before_request
def setup():
    pass


@app.route("/chat", methods=["POST"])
def chat():
    # This is the core endpoint where the Natural Language Interface (UI)
    # sends the user's text. We extract the message and pass it to the Inference Engine.
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "No message provided"}), 400
    user_input = str(data["message"])[:500]  # cap input length
    
    # Passing the input to Tier 2 (Inference Engine) to process the NLP.
    response = get_response(user_input)
    
    return jsonify({"response": response})


# --- Admin: self-learning endpoints ---
@app.route("/admin/unknown", methods=["GET"])
def admin_unknown():
    queries = get_unanswered_queries()
    return jsonify(queries)


@app.route("/admin/teach", methods=["POST"])
def admin_teach():
    # Machine Learning / Self-Learning mechanism.
    # This endpoint allows an admin to map an unknown query to a specific response.
    # It stores this in the Knowledge Base, making the bot "smarter" over time.
    data = request.get_json()
    trigger = data.get("trigger", "").strip()
    response = data.get("response", "").strip()
    if not trigger or not response:
        return jsonify({"error": "trigger and response required"}), 400
    add_learned_response(trigger, response)
    return jsonify({"success": True, "message": f"Bot learned: '{trigger}' → response saved."})


@app.route("/admin/packages", methods=["GET"])
def admin_packages():
    return jsonify(get_all_packages())


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
