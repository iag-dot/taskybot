from flask import Flask, request, jsonify
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
import os

# Initialize Slack app using environment variables
slack_app = App(
    token=os.environ["SLACK_BOT_TOKEN"],
    signing_secret=os.environ["SLACK_SIGNING_SECRET"]
)

# Initialize Flask app
flask_app = Flask(__name__)
handler = SlackRequestHandler(slack_app)

# Slack event route
@flask_app.route("/slack/events", methods=["GET", "POST"])
def slack_events():
    if request.headers.get("Content-Type") == "application/json":
        data = request.get_json()
        if "challenge" in data:
            return jsonify({"challenge": data["challenge"]}), 200
    return handler.handle(request)

# Optional mention response
@slack_app.event("app_mention")
def mention_handler(event, say):
    say("👋 Hello from TaskyBot!")

# Start the Flask app
if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=5000)