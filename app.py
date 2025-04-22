from flask import Flask, request, jsonify
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_bolt.oauth.oauth_settings import OAuthSettings
from datetime import datetime, timedelta
from supabase_handler import insert_task
import os

from dotenv import load_dotenv
load_dotenv()

# Slack and Flask setup
slack_app = App(
    token=os.environ["SLACK_BOT_TOKEN"],
    signing_secret=os.environ["SLACK_SIGNING_SECRET"]
)
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

# Slash command: /assign
@slack_app.command("/assign")
def handle_assign(ack, body, client, respond):
    ack()
    trigger_id = body["trigger_id"]
    assigner = body["user_name"]
    text = body.get("text", "")

    if not text:
        respond("Please include task details like: `/assign @john Do the thing by 6PM`")
        return

    # Ask the assignee how much time they need
    client.views_open(
        trigger_id=trigger_id,
        view={
            "type": "modal",
            "callback_id": "task_modal",
            "title": {"type": "plain_text", "text": "Task Estimate"},
            "submit": {"type": "plain_text", "text": "Submit"},
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
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "input",
                        "placeholder": {"type": "plain_text", "text": "e.g. 3.5 (in hours)"}
                    },
                    "label": {"type": "plain_text", "text": "How much time will this take?"}
                },
                {
                    "type": "input",
                    "block_id": "deadline",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "input",
                        "placeholder": {"type": "plain_text", "text": "e.g. 2025-04-22 17:30"}
                    },
                    "label": {"type": "plain_text", "text": "Deadline (YYYY-MM-DD HH:MM)"}
                }
            ]
        }
    )

# Modal submission handler
@slack_app.view("task_modal")
def handle_modal_submission(ack, body, view, client):
    ack()
    state_values = view["state"]["values"]

    task_text = state_values["task_text"]["input"]["value"]
    assignee = state_values["assignee"]["input"]["value"]
    estimated = float(state_values["estimated_time"]["input"]["value"])
    deadline_str = state_values["deadline"]["input"]["value"]
    assigner = body["user"]["name"]

    # Parse deadline
    deadline = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M")
    slack_ts = view["id"]

    # Store task in Supabase
    insert_task(task_text, assigner, assignee, estimated, deadline.isoformat(), slack_ts)

    # Notify assigner
    client.chat_postMessage(
        channel=f"@{assigner}",
        text=(
            f"✅ Task created and assigned to @{assignee}!

"
            f"*Task:* {task_text}
"
            f"*Est. Time:* {estimated} hrs
"
            f"*Deadline:* {deadline_str}"
        )
    )

# Run Flask app
if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=5000)