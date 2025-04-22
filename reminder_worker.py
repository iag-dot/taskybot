import os
from datetime import datetime, timedelta
from supabase import create_client
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

load_dotenv()

# Supabase client setup
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Slack client setup
slack = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))

def send_reminder(user, message):
    try:
        slack.chat_postMessage(channel=f"@{user}", text=message)
        print(f"✅ Sent message to @{user}")
    except SlackApiError as e:
        print(f"❌ Error sending message to {user}: {e.response['error']}")

def check_tasks_and_remind():
    now = datetime.utcnow()
    time_windows = {
        "3hr": now + timedelta(hours=3),
        "1hr": now + timedelta(hours=1),
        "10min": now + timedelta(minutes=10),
        "due": now
    }

    print(f"📆 Checking tasks at {now.isoformat()}")

    tasks = supabase.table("tasks").select("*").eq("status", "pending").execute().data

    for task in tasks:
        task_time = datetime.fromisoformat(task["deadline"])
        assignee = task["assignee"]
        message = None

        for label, reminder_time in time_windows.items():
            time_diff = abs((task_time - reminder_time).total_seconds())
            if time_diff < 180:
                if label == "due":
                    message = (
                        f"⏰ Hey @{assignee}, your task is now due!\n"
                        f"*Task:* {task['task_text']}\n\n"
                        f"Is it done?"
                    )
                else:
                    message = (
                        f"🔔 Reminder: Your task is due in {label}.\n"
                        f"*Task:* {task['task_text']}"
                    )
                break

        if message:
            send_reminder(assignee, message)

if __name__ == "__main__":
    check_tasks_and_remind()
