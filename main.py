import json
import requests
import os
import time
import feedparser

# Load config
with open("config.json", "r") as f:
    config = json.load(f)

queries = config["queries"]
webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

if webhook_url is None:
    raise ValueError("Missing DISCORD_WEBHOOK_URL environment variable")

def fetch_and_post():
    for q in queries:
        query = q["search_query"]
        name = q["name"]
        max_results = q.get("max_results", 5)

        print(f"📡 Querying: {name}")
        url = f"http://export.arxiv.org/api/query?search_query={query}&start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
        feed = feedparser.parse(url)

        for entry in feed.entries:
            title = entry.title
            link = entry.link
            authors = ", ".join(a.name for a in entry.authors)
            summary = entry.summary[:300] + "..."

            content = f"**📝 {title}**\n👤 *{authors}*\n🔗 {link}"
            payload = {"content": content}

            res = requests.post(webhook_url, json=payload)
            print(f"Posted: {title} → status {res.status_code}")
            time.sleep(1)

fetch_and_post()
