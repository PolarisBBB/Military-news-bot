print("🚨 NEW VERSION RUNNING")
print("🚨 THIS IS NEW BOT FILE")
import os
import requests
import feedparser
import json

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

STATE_FILE = "state.json"

RSS_FEEDS = [
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://feeds.skynews.com/feeds/rss/world.xml"
]


def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": True
    })


def get_all_news():
    news = []

    for url in RSS_FEEDS:
        feed = feedparser.parse(url)

        for entry in feed.entries[:3]:
            news.append({
                "title": entry.title,
                "link": entry.link
            })

    return news


def main():
    news = get_all_news()

    for item in news[:5]:
        send_message(f"📰 {item['title']}\n\n{item['link']}")


if __name__ == "__main__":
    main()
