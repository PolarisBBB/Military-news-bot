import os
import requests
import feedparser
import json
import re
from datetime import datetime

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

STATE_FILE = "state.json"

RSS_FEEDS = [
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://feeds.skynews.com/feeds/rss/world.xml"
]

# 🌍 театры
THEATERS = {
    "europe": ["russia", "ukraine", "nato", "europe", "poland", "germany", "france"],
    "asia": ["china", "taiwan", "japan", "korea", "india", "philippines", "vietnam"],
    "middle_east": ["iran", "israel", "syria", "iraq", "yemen"],
    "global_military": ["war", "missile", "drone", "tank", "submarine", "fighter", "defense"]
}

# 🔥 ключевые события
HIGH_IMPACT = [
    "war", "attack", "strike", "invasion", "mobilization",
    "missile", "nuclear", "crash", "killed", "battle",
    "exercise", "drill", "agreement", "summit", "visit"
]


def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {"seen": []}


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


# 🧠 определение театра
def detect_theater(text):
    t = text.lower()

    for theater, keywords in THEATERS.items():
        if any(k in t for k in keywords):
            return theater

    return "global"


# 🔥 важность
def get_priority(text):
    t = text.lower()
    return 3 if any(k in t for k in HIGH_IMPACT) else 2


# 🧹 очистка заголовка
def clean_title(title):
    title = re.sub(r"\s-\s.*$", "", title)
    title = re.sub(r"\s+", " ", title).strip()
    return title[:160]


# 📰 новости
def get_news():
    news = []

    for url in RSS_FEEDS:
        feed = feedparser.parse(url)

        for entry in feed.entries[:5]:
            news.append({
                "title": entry.title,
                "link": entry.link
            })

    return news


def main():
    state = load_state()
    seen = state.get("seen", [])

    news = get_news()

    for item in news:

        if item["link"] in seen:
            continue

        text = item["title"].lower()

        # фильтр мусора
        if len(text) < 30:
            continue

        theater = detect_theater(text)
        priority = get_priority(text)

        # OSINT формат
        summary = clean_title(item["title"])

        stamp = "🔥" * priority

        message = f"""📡 OSINT UPDATE [{theater.upper()}]

{stamp} {summary}

🔗 Source: {item['link']}"""

        send_message(message)

        print("Sent:", summary)

        seen.append(item["link"])

    state["seen"] = seen[-300:]
    save_state(state)


if __name__ == "__main__":
    main()
