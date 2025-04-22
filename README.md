# TaskyBot

A Slack bot that receives events and responds to mentions. Built using Flask + Slack Bolt. Ready for deployment on Render.com

## How to deploy on Render

1. Create a free account on [Render](https://render.com/)
2. Create a new Web Service and connect this repo.
3. Set the build command to:

```
pip install -r requirements.txt
```

4. Set the start command to:

```
python app.py
```

5. Add environment variables:
- `SLACK_BOT_TOKEN`
- `SLACK_SIGNING_SECRET`