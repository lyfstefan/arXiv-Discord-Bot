import json
import requests
import os
import time
import feedparser
from pathlib import Path
from datetime import datetime, timedelta
from urllib.parse import quote  

# Load search queries and bot settings
with open("config.json", "r") as f:
    config = json.load(f)

queries = config["queries"]
webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

if webhook_url is None:
    raise ValueError("Missing DISCORD_WEBHOOK_URL environment variable")

# Setup a cache to avoid duplicate posts
CACHE_DIR = Path(".cache")
CACHE_FILE = CACHE_DIR / "arxiv_sent_ids.txt"
CACHE_DIR.mkdir(exist_ok=True)
if not CACHE_FILE.exists():
    CACHE_FILE.write_text("")

sent_ids = set(CACHE_FILE.read_text().splitlines())

# Only include papers published within the last 7 days
cutoff_date = datetime.utcnow() - timedelta(days=7)

def fetch_and_post():
    new_ids = []

    for q in queries:
        query = q["search_query"]
        name = q["name"]
        max_results = q.get("max_results", 5)

        print(f"📡 Querying: {name}")
        encoded_query = quote(query)

        url = f"http://export.arxiv.org/api/query?search_query={encoded_query}&start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
        feed = feedparser.parse(url)

        for entry in feed.entries:
            entry_id = entry.id.strip()

            if entry_id in sent_ids:
                print(f"⏩ Skipping already-sent: {entry.title}")
                continue

            published = datetime(*entry.published_parsed[:6])
            if published < cutoff_date:
                print(f"⏩ Skipping old paper: {entry.title} (published {published})")
                continue

            title = entry.title
            link = entry.link
            authors = ", ".join(a.name for a in entry.authors)
            summary = entry.summary[:300] + "..."

            content = f"**📝 {title}**\n👤 *{authors}*\n🔗 {link}\n🗂️ `{name}`"
            payload = {"content": content}

            res = requests.post(webhook_url, json=payload)
            print(f"✅ Posted: {title} → {res.status_code}")

            new_ids.append(entry_id)
            time.sleep(1)

    # Update cache
    if new_ids:
        with open(CACHE_FILE, "a") as f:
            for id in new_ids:
                f.write(id + "\n")

fetch_and_post()
