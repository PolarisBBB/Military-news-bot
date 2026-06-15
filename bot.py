import os
import requests
import feedparser
import json

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

STATE_FILE = "state.json"

# 📡 Несколько источников новостей
RSS_FEEDS = [
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://feeds.skynews.com/feeds/rss/world.xml"
]
]


def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


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


def get_all_news():
    all_news = []

    for url in RSS_FEEDS:
        print("Checking:", url)

        feed = feedparser.parse(url)

        print("Entries:", len(feed.entries))

        for entry in feed.entries[:3]:
            print("TITLE:", entry.title)

            all_news.append({
                "title": entry.title,
                "link": entry.link
            })

    return all_news

    for url in RSS_FEEDS:
        feed = feedparser.parse(url)

        for entry in feed.entries[:5]:
            all_news.append({
                "title": entry.title,
                "link": entry.link
            })

    return all_news


def main():
    seen = []

    news = get_all_news()

    new_items = []

    for item in news:
        if item["link"] not in seen:
            new_items.append(item)

    if not new_items:
        print("No new news")
        return

    for item in new_items[:10]:
        message = f"📰 {item['title']}\n\n{item['link']}"
        send_message(message)
        print("Sent:", item["title"])

        seen.append(item["link"])

    state["seen"] = seen[-200:]  # ограничим память
    save_state(state)


if __name__ == "__main__":
    main()
