from flask import Flask, request, jsonify
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from datetime import datetime
from dotenv import load_dotenv
import os
from supabase import create_client
from supabase_handler import insert_task  # must have this file next to app.py

load_dotenv()

# Slack credentials from environment
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")

# Supabase (optional check)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize Slack Bolt app
slack_app = App(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET)

# Flask app
flask_app = Flask(__name__)
handler = SlackRequestHandler(slack_app)

# Slack event endpoint
@flask_app.route("/slack/events", methods=["GET", "POST"])
def slack_events():
    if request.method == "POST" and request.headers.get("Content-Type") == "application/json":
        data = request.get_json()
        if "challenge" in data:
            return jsonify({"challenge": data["challenge"]}), 200
    return handler.handle(request)

# /assign command → open modal
@slack_app.command("/assign")
def assign_command(ack, body, client):
    ack()
    trigger_id = body["trigger_id"]

    client.views_open(
        trigger_id=trigger_id,
        view={
            "type": "modal",
            "callback_id": "task_modal",
            "title": {"type": "plain_text", "text": "Assign a Task"},
            "submit": {"type": "plain_text", "text": "Save"},
            "blocks": [
                {
                    "type": "input",
                    "block_id": "task_text",
                    "element": {"type": "plain_text_input", "action_id": "input"},
                    "label": {"type": "plain_text", "text": "What is the task?"}
                },
                {
                    "type": "input",
                    "block_id": "assignee",
                    "element": {"type": "plain_text_input", "action_id": "input"},
                    "label": {"type": "plain_text", "text": "Who is this assigned to?"}
                },
                {
                    "type": "input",
                    "block_id": "estimated_time",
                    "element": {"type": "plain_text_input", "action_id": "input"},
                    "label": {"type": "plain_text", "text": "Estimated time (in hours)"}
                },
                {
                    "type": "input",
                    "block_id": "deadline",
                    "element": {"type": "plain_text_input", "action_id": "input"},
                    "label": {"type": "plain_text", "text": "Deadline (YYYY-MM-DD HH:MM)"}
                }
            ]
        }
    )

# Modal submission handler
@slack_app.view("task_modal")
def handle_modal(ack, body, view, client):
    ack()
    state = view["state"]["values"]

    task_text = state["task_text"]["input"]["value"]
    assignee = state["assignee"]["input"]["value"]
    estimated = float(state["estimated_time"]["input"]["value"])
    deadline_str = state["deadline"]["input"]["value"]
    assigner = body["user"]["name"]
    deadline = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M")
    slack_ts = view["id"]

    # Store task in Supabase
    insert_task(task_text, assigner, assignee, estimated, deadline.isoformat(), slack_ts)

    # Confirm to assigner
    message = (
        f"✅ Task created and assigned to @{assignee}!\n\n"
        f"*Task:* {task_text}\n"
        f"*Est. Time:* {estimated} hrs\n"
        f"*Deadline:* {deadline_str}"
    )
    client.chat_postMessage(channel=f"@{assigner}", text=message)

# Start Flask app
if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=5000)
