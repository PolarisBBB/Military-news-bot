import os
import requests
import feedparser
import json
from datetime import datetime

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

RSS_URL = "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"

STATE_FILE = "state.json"


def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {"last_title": ""}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": True
    })


def get_news():
    feed = feedparser.parse(RSS_URL)
    return feed.entries[:5]


def main():
    state = load_state()
    last_title = state.get("last_title", "")

    news = get_news()

    new_items = []

    for item in news:
        if item.title == last_title:
            break
        new_items.append(item)

    if not new_items:
        print("No new news")
        return

    for item in reversed(new_items):
        message = f"📰 {item.title}\n\n{item.link}"
        send_message(message)
        print("Sent:", item.title)

    state["last_title"] = news[0].title
    save_state(state)


if __name__ == "__main__":
    main()
