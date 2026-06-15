import os
import requests
import feedparser
import json
import re

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

STATE_FILE = "state.json"


# =========================
# 🌍 FULL OSINT SOURCE MATRIX (TVD STYLE)
# =========================
RSS_FEEDS = [

    # GLOBAL WIRE SERVICES
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.reuters.com/world/rss",
    "https://apnews.com/hub/ap-top-news/rss",
    "https://www.aljazeera.com/xml/rss/all.xml",

    # EUROPE / NATO CORE
    "https://www.france24.com/en/rss",
    "https://www.dw.com/en/top-stories/s-9097",
    "https://www.euronews.com/rss?level=theme&name=news",

    # USA DEFENCE / POLICY
    "https://www.defensenews.com/arc/outboundfeeds/rss/",
    "https://breakingdefense.com/feed/",
    "https://www.politico.com/rss/politicopicks.xml",

    # UK
    "https://news.sky.com/feeds/rss/world.xml",
    "https://www.telegraph.co.uk/news/rss.xml",

    # UKRAINE / WAR ZONE
    "https://www.ukrinform.net/rss/block-lastnews",
    "https://kyivindependent.com/feed/",

    # ASIA PACIFIC
    "https://www3.nhk.or.jp/nhkworld/en/news/rss/",
    "https://en.yna.co.kr/RSS/news.xml",
    "https://www.japantimes.co.jp/feed/",

    # CHINA / STATE MEDIA
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

    # DEFENCE / OSINT SPECIALIZED
    "https://www.navalnews.com/feed/",
    "https://www.airforce-technology.com/feed/",
    "https://www.armyrecognition.com/rss/news",
    "https://www.janes.com/feeds/rss",  # (may be partial access depending region)

    # ADDITIONAL STRATEGIC OSINT
    "https://www.atlanticcouncil.org/feed/",
    "https://www.csis.org/rss.xml",
]


# =========================
# CLASSIFICATION ENGINE
# =========================
CRITICAL = [
    "war", "attack", "strike", "missile", "drone",
    "invasion", "battle", "crash", "killed"
]

HIGH = [
    "contract", "deal", "agreement", "delivery",
    "tank", "jet", "fighter", "submarine", "ship",
    "exercise", "drill", "summit"
]

MED = [
    "visit", "meeting", "talks", "cooperation"
]


# =========================
# REGION DETECTION (TVD STYLE)
# =========================
REGIONS = {
    "NATO/EUROPE": ["nato", "europe", "germany", "france", "poland", "uk"],
    "UKRAINE FRONT": ["ukraine", "kyiv", "russia"],
    "ASIA-PACIFIC": ["china", "japan", "korea", "taiwan", "philippines", "india"],
    "MIDDLE EAST": ["iran", "israel", "syria", "iraq"],
    "GLOBAL": []
}


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


# =========================
# ANALYTICS LAYER (TVD CORE)
# =========================
def get_region(text):
    t = text.lower()
    for region, keys in REGIONS.items():
        if any(k in t for k in keys):
            return region
    return "GLOBAL"


def get_level(text):
    t = text.lower()
    if any(k in t for k in CRITICAL):
        return "CRITICAL"
    if any(k in t for k in HIGH):
        return "HIGH"
    if any(k in t for k in MED):
        return "MEDIUM"
    return "LOW"


def clean(text):
    text = re.sub(r"\s+", " ", text)
    return text[:180]


# =========================
# NEWS AGGREGATION
# =========================
def get_news():
    items = []

    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)

            for e in feed.entries[:5]:
                items.append({
                    "title": e.title,
                    "link": e.link
                })

        except:
            continue

    return items


# =========================
# MAIN ENGINE
# =========================
def main():
    state = load_state()
    seen = state["seen"]

    news = get_news()

    for item in news:

        if item["link"] in seen:
            continue

        title = item["title"]

        region = get_region(title)
        level = get_level(title)

        # фильтр мусора
        if level == "LOW":
            continue

        summary = clean(title)

        emoji = {
            "CRITICAL": "🔴",
            "HIGH": "🟠",
            "MEDIUM": "🟡"
        }.get(level, "⚪")

        message = f"""📡 TVD OSINT REPORT [{region}] [{level}]

{emoji} {summary}

🔗 {item['link']}"""

        send_message(message)

        print("SENT:", summary)

        seen.append(item["link"])

    state["seen"] = seen[-500:]
    save_state(state)


if __name__ == "__main__":
    main()
