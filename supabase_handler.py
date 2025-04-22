from supabase import create_client, Client
import os

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def insert_task(task_text, assigner, assignee, estimated_hrs, deadline, slack_ts):
    data = {
        "task_text": task_text,
        "assigner": assigner,
        "assignee": assignee,
        "estimated_hrs": estimated_hrs,
        "deadline": deadline,
        "status": "pending",
        "slack_ts": slack_ts
    }
    return supabase.table("tasks").insert(data).execute()