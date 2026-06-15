import os
import requests
import feedparser
import json
import re
from datetime import datetime, timedelta
from urllib.parse import quote

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

STATE_FILE = "state.json"


# =========================
# RSS SOURCES (оставил MAX OSINT)
# =========================
RSS_FEEDS = [
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.reuters.com/world/rss",
    "https://apnews.com/hub/ap-top-news/rss",
    "https://www.aljazeera.com/xml/rss/all.xml",

    "https://www.defensenews.com/arc/outboundfeeds/rss/",
    "https://breakingdefense.com/feed/",
    "https://www.navalnews.com/feed/",
    "https://www.armyrecognition.com/rss/news",
    "https://www.airforce-technology.com/feed/",

    "https://kyivindependent.com/feed/",
    "https://www.japantimes.co.jp/feed/",
    "https://en.yna.co.kr/RSS/news.xml",
    "http://www.xinhuanet.com/english/rss/worldrss.xml",
    "https://indianexpress.com/section/world/feed/",
]


# =========================
# ЖЁСТКИЙ ФИЛЬТР ВОЕННЫХ ТЕМ
# =========================
ALLOW = [
    "war", "military", "army", "navy", "air force",
    "weapon", "tank", "jet", "missile", "drone",
    "defense", "defence", "exercise", "drill",
    "contract", "deal", "agreement", "arms",
    "bomber", "fighter", "submarine", "fleet"
]

BLOCK = [
    "actor", "singer", "music", "celebrity",
    "crash", "accident", "helicopter crash",
    "football", "sport", "game",
    "opinion", "analysis", "think", "commentary"
]


# =========================
# STATE
# =========================
def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {"seen": []}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


# =========================
# TRANSLATE (FREE)
# =========================
def translate(text):
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=ru&dt=t&q={quote(text)}"
        r = requests.get(url)
        return r.json()[0][0][0]
    except:
        return text


# =========================
# CLEAN
# =========================
def clean(text):
    return re.sub(r"\s+", " ", text).strip()[:220]


# =========================
# TIME FILTER (24H)
# =========================
def is_recent(entry):
    try:
        t = entry.published_parsed
        dt = datetime(*t[:6])
        return datetime.utcnow() - dt < timedelta(hours=24)
    except:
        return True


# =========================
# COUNTRY MAP
# =========================
def country(text):
    t = text.lower()

    m = {
        "США": ["us", "usa", "pentagon"],
        "Украина": ["ukraine", "kyiv"],
        "Россия": ["russia"],
        "Франция": ["france"],
        "Германия": ["germany"],
        "Китай": ["china"],
        "Япония": ["japan"],
        "Корея": ["korea"],
        "Индия": ["india"],
        "Иран": ["iran"],
    }

    for k, v in m.items():
        if any(x in t for x in v):
            return k
    return "Мир"


# =========================
# SEND
# =========================
def send(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})


# =========================
# NEWS
# =========================
def get_news():
    out = []

    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)

            for e in feed.entries[:5]:
                if not is_recent(e):
                    continue

                title = e.title.lower()

                # ❌ блок мусора
                if any(b in title for b in BLOCK):
                    continue

                # ❌ только военка
                if not any(a in title for a in ALLOW):
                    continue

                out.append({
                    "title": e.title,
                    "link": e.link
                })

        except:
            continue

    return out


# =========================
# MAIN
# =========================
def main():
    state = load_state()
    seen = state["seen"]

    news = get_news()

    for n in news:

        if n["link"] in seen:
            continue

        c = country(n["title"])
        title_ru = translate(n["title"])
        title_ru = clean(title_ru)

        message = f"""{c}

📰 {title_ru}

🔗 {n['link']}"""

        send(message)

        print("SENT:", title_ru)

        seen.append(n["link"])

    state["seen"] = seen[-500:]
    save_state(state)


if __name__ == "__main__":
    main()
