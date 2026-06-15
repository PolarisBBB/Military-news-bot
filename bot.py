import os
import requests
import feedparser
import json
import re

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

STATE_FILE = "state.json"

RSS_FEEDS = [
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://feeds.skynews.com/feeds/rss/world.xml"
]

# 🎯 ключевые военные/политические темы
KEYWORDS_HIGH = [
    "war", "attack", "missile", "airstrike", "battle",
    "invasion", "drone", "tank", "fighter", "submarine",
    "warship", "nuclear", "mobilization", "defense"
]

KEYWORDS_MED = [
    "agreement", "deal", "summit", "meeting", "visit",
    "exercise", "drill", "contract", "delivery", "aid",
    "sanctions", "cooperation"
]

COUNTRIES = [
    "USA", "United States", "Ukraine", "Russia", "NATO",
    "China", "Taiwan", "Japan", "South Korea", "North Korea",
    "India", "Iran", "Australia", "Vietnam", "Philippines",
    "Azerbaijan"
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


# 🧠 определяем важность
def get_priority(text):
    t = text.lower()

    if any(k in t for k in KEYWORDS_HIGH):
        return 3  # 🔥🔥🔥
    elif any(k in t for k in KEYWORDS_MED):
        return 2  # 🔥🔥
    else:
        return 1  # 🔥


# 🎯 фильтр интереса
def is_interesting(text):
    t = text.lower()
    return any(k.lower() in t for k in KEYWORDS_HIGH + KEYWORDS_MED + COUNTRIES)


# ✂️ умное сокращение (как OSINT-канал)
def smart_summary(title):
    title = re.sub(r"\s+", " ", title).strip()

    # убираем лишние хвосты
    title = re.sub(r"\s-\s.*$", "", title)

    if len(title) > 160:
        title = title[:160] + "..."

    return title


# 📰 новости
def get_all_news():
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

    news = get_all_news()

    for item in news:

        if item["link"] in seen:
            continue

        text = item["title"]

        if not is_interesting(text):
            continue

        priority = get_priority(text)

        summary = smart_summary(text)

        prefix = "🔥" * priority

        message = f"""{prefix} {summary}

🔗 {item['link']}"""

        send_message(message)
        print("Sent:", summary)

        seen.append(item["link"])

    state["seen"] = seen[-300:]
    save_state(state)


if __name__ == "__main__":
    main()
