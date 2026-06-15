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

# 🧠 интересующие темы
KEYWORDS = [
    "military", "war", "defense", "weapon", "tank", "fighter",
    "aircraft", "drone", "missile", "submarine", "warship",
    "exercise", "drill", "agreement", "deal", "summit",
    "visit", "meeting", "crash", "killed", "accident"
]

COUNTRIES = [
    "USA", "United States", "Ukraine", "Russia", "NATO",
    "Japan", "South Korea", "North Korea", "China",
    "Taiwan", "India", "Iran", "Australia", "Vietnam",
    "Philippines", "Azerbaijan"
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


# 🔍 фильтр интересных новостей
def is_interesting(text):
    text_lower = text.lower()
    return any(k.lower() in text_lower for k in KEYWORDS + COUNTRIES)


# 📰 сбор новостей
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


# ✂️ простое "резюме" без AI
def create_summary(title):
    # просто чистим и укорачиваем заголовок
    if len(title) > 140:
        title = title[:140] + "..."

    return title


def main():
    state = load_state()
    seen = state.get("seen", [])

    news = get_all_news()

    for item in news:

        if item["link"] in seen:
            continue

        full_text = item["title"]

        if not is_interesting(full_text):
            continue

        summary = create_summary(full_text)

        message = f"""🔥 {summary}

🔗 {item['link']}"""

        send_message(message)
        print("Sent:", summary)

        seen.append(item["link"])

    state["seen"] = seen[-200:]
    save_state(state)


if __name__ == "__main__":
    main()
