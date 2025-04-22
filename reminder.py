import os
from datetime import datetime, timedelta
from supabase import create_client
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
slack = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))

def send_reminder(user, message):
    try:
        slack.chat_postMessage(channel=f"@{user}", text=message)
        print("✅ Sent message to @" + user)
    except SlackApiError as e:
        print("❌ Error sending message to " + user + ": " + e.response['error'])

def check_tasks_and_remind():
    now = datetime.utcnow()
    windows = {
        "3hr": now + timedelta(hours=3),
        "1hr": now + timedelta(hours=1),
        "10min": now + timedelta(minutes=10),
        "due": now
    }

    print("📆 Checking tasks at", now.isoformat())

    tasks = supabase.table("tasks").select("*").eq("status", "pending").execute().data

    for task in tasks:
        task_time = datetime.fromisoformat(task["deadline"])
        assignee = task["assignee"]
        message = None

        for label, time in windows.items():
            if abs((task_time - time).total_seconds()) < 180:
                if label == "due":
                    message = (
                        "⏰ Hey @" + assignee + ", your task is now due!\\n*Task:* " +
                        task["task_text"] + "\\n\\nIs it done?"
                    )
                else:
                    message = (
                        "🔔 Reminder: Your task is due in " + label + ".\\n*Task:* " +
                        task["task_text"]
                    )
                break

        if message:
            send_reminder(assignee, message)

if __name__ == "__main__":
    check_tasks_and_remind()
