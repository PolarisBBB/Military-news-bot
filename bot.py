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
# 🌍 MAX OSINT SOURCE MATRIX
# =========================
RSS_FEEDS = [

    # GLOBAL WIRE
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.reuters.com/world/rss",
    "https://apnews.com/hub/ap-top-news/rss",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://www.france24.com/en/rss",
    "https://www.dw.com/en/top-stories/s-9097",
    "https://www.euronews.com/rss?level=theme&name=news",

    # USA / NATO DEFENCE
    "https://www.defensenews.com/arc/outboundfeeds/rss/",
    "https://breakingdefense.com/feed/",
    "https://www.politico.com/rss/politicopicks.xml",
    "https://www.npr.org/rss/rss.php?id=1004",

    # UK
    "https://news.sky.com/feeds/rss/world.xml",
    "https://www.telegraph.co.uk/news/rss.xml",

    # UKRAINE / WAR ZONE
    "https://www.ukrinform.net/rss/block-lastnews",
    "https://kyivindependent.com/feed/",

    # ASIA
    "https://www3.nhk.or.jp/nhkworld/en/news/rss/",
    "https://en.yna.co.kr/RSS/news.xml",
    "https://www.japantimes.co.jp/feed/",

    # CHINA
    "http://www.xinhuanet.com/english/rss/worldrss.xml",
    "https://www.globaltimes.cn/rss/outbrain.xml",

    # INDIA
    "https://indianexpress.com/section/world/feed/",
    "https://www.thehindu.com/news/international/?service=rss",

    # IRAN
    "https://en.irna.ir/rss",

    # AUSTRALIA
    "https://www.abc.net.au/news/feed/46182/rss.xml",

    # PHILIPPINES
    "https://www.pna.gov.ph/rss/news.xml",

    # DEFENCE OSINT
    "https://www.navalnews.com/feed/",
    "https://www.airforce-technology.com/feed/",
    "https://www.armyrecognition.com/rss/news",

    # ANALYTICS / THINK TANKS
    "https://www.csis.org/rss.xml",
    "https://www.atlanticcouncil.org/feed/",

    # EXTRA OSINT (loss tracking / military analysis)
    "https://www.oryxspioenkop.com/feeds/posts/default?alt=rss"
]


# =========================
# FILTER LOGIC (NEWS ONLY)
# =========================
CRITICAL = ["war", "attack", "strike", "missile", "drone", "crash", "killed"]
HIGH = ["contract", "deal", "agreement", "delivery", "tank", "jet", "submarine", "ship", "exercise"]
MED = ["meeting", "visit", "talks", "summit"]


# =========================
# COUNTRY DETECTION
# =========================
def get_country(text):
    t = text.lower()

    map_ = {
        "США": ["us", "usa", "pentagon", "america"],
        "Украина": ["ukraine", "kyiv"],
        "Россия": ["russia", "moscow"],
        "Франция": ["france"],
        "Германия": ["germany"],
        "Китай": ["china"],
        "Япония": ["japan"],
        "Южная Корея": ["korea"],
        "Индия": ["india"],
        "Иран": ["iran"],
    }

    for k, v in map_.items():
        if any(x in t for x in v):
            return k

    return "Мир"


# =========================
# TIME FILTER (24 HOURS ONLY)
# =========================
def is_recent(entry):
    try:
        published = entry.published_parsed
        pub_time = datetime(*published[:6])
        return datetime.utcnow() - pub_time < timedelta(hours=24)
    except:
        return True


# =========================
# CLEAN TEXT
# =========================
def clean(text):
    text = re.sub(r"\s+", " ", text)
    return text.strip()[:220]


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
# SEND
# =========================
def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": True
    })


# =========================
# NEWS FETCH
# =========================
def get_news():
    items = []

    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)

            for e in feed.entries[:5]:
                if not is_recent(e):
                    continue

                items.append({
                    "title": e.title,
                    "link": e.link
                })

        except:
            continue

    return items


# =========================
# MAIN
# =========================
def main():
    state = load_state()
    seen = state["seen"]

    news = get_news()

    for item in news:

        if item["link"] in seen:
            continue

        country = get_country(item["title"])

        title = clean(item["title"])

        # фильтр мусора
        low = title.lower()
        if not any(k in low for k in CRITICAL + HIGH + MED):
            continue

        message = f"""{country}

📰 {title}

🔗 {item['link']}"""

        send_message(message)

        print("SENT:", title)

        seen.append(item["link"])

    state["seen"] = seen[-600:]
    save_state(state)


if __name__ == "__main__":
    main()
