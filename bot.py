import os
import requests
import feedparser
import json
from datetime import datetime, timedelta
from urllib.parse import quote

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

STATE_FILE = "state.json"


# =========================
# RSS SOURCES (DEFENCE OSINT)
# =========================
RSS_FEEDS = [

    # Мировые СМИ
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",

    # Военные СМИ
    "https://www.defensenews.com/arc/outboundfeeds/rss/",
    "https://breakingdefense.com/feed/",
    "https://www.navalnews.com/feed/",
    "https://www.armyrecognition.com/rss/news",
    "https://www.airforce-technology.com/feed/",
    "https://www.navalnews.com/feed/",

    # Новые источники
    "https://www.thedefensenews.com/feed/",
    "https://www.fmv.se/rss.xml",

    # Азия
    "https://www.japantimes.co.jp/feed/",
    "https://en.yna.co.kr/RSS/news.xml",

]



# =========================
# OFFICIAL SOURCES DIRECTORY
# =========================
OFFICIAL_SOURCES = {
    "НАТО": "https://www.nato.int/",
    "Минобороны США": "https://www.defense.gov/",
    "Армия США": "https://www.army.mil/",
    "ВМС США": "https://www.navy.mil/",
    "Корпус морской пехоты США": "https://www.marines.mil/",
    "DARPA": "https://www.darpa.mil/",
    "AFRL": "https://www.afresearchlab.com/",
    "Rheinmetall": "https://www.rheinmetall.com/",
    "BAE Systems": "https://www.baesystems.com/",
    "Leonardo": "https://www.leonardo.com/",
    "Saab": "https://www.saab.com/",
    "Thales": "https://www.thalesgroup.com/",
    "Patria": "https://www.patria.fi/",
    "KNDS": "https://www.knds.com/",
    "Lockheed Martin": "https://www.lockheedmartin.com/",
    "Northrop Grumman": "https://www.northropgrumman.com/",
    "RTX": "https://www.rtx.com/",
    "General Dynamics": "https://www.gd.com/",
    "Airbus Defence": "https://www.airbus.com/en/products-services/defence",
    "Европейское оборонное агентство": "https://eda.europa.eu/",
    "Минобороны Азербайджана": "https://mod.gov.az/",
    "DOT&E": "https://www.dote.osd.mil/",
    "US STRATCOM": "https://www.stratcom.mil/",
}


# =========================
# FILTERS (MILITARY OSINT ONLY)
# =========================
ALLOW = [
    "military", "army", "navy", "air force",
    "tank", "jet", "fighter", "bomber",
    "missile", "drone", "submarine",
    "defense", "defence", "weapon",
    "contract", "deal", "agreement",
    "exercise", "drill", "deployment"
]

BLOCK = [

    "interview",
    "exclusive interview",
    "q&a",
    "analysis",
    "opinion",
    "editorial",
    "podcast",
    "video",

    "celebrity",
    "actor",
    "singer",
    "music",
    "movie",
    "film",
    "festival",
    "football",
    "soccer",
    "basketball",
    "baseball",
    "tennis",
    "olympics",
    "entertainment",
    "hollywood",
    "crime",
    "murder",
    "weather",
    "wildfire",

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
# TRANSLATION (FREE API)
# =========================
def translate(text):
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=ru&dt=t&q={quote(text)}"
        r = requests.get(url)
        return r.json()[0][0][0]
    except:
        return text


# =========================
# CLEAN TEXT
# =========================
def clean(text):
    return " ".join(text.split())[:240]


# =========================
# TIME FILTER (24h)
# =========================
def is_recent(entry):
    try:
        t = entry.published_parsed
        dt = datetime(*t[:6])
        return datetime.utcnow() - dt < timedelta(hours=24)
    except:
        return True


# =========================
# COUNTRY DETECTION
# =========================
def detect_country(text):
    t = text.lower()

    mapping = {
        "США": ["usa", "us ", "pentagon"],
        "Украина": ["ukraine", "kyiv"],
        "Россия": ["russia"],
        "Китай": ["china"],
        "Япония": ["japan"],
        "Корея": ["korea"],
        "Индия": ["india"],
        "Иран": ["iran"],
        "Франция": ["france"],
        "Германия": ["germany"],
    }

    for k, v in mapping.items():
        if any(x in t for x in v):
            return k

    return "Мир"


# =========================
# OFFICIAL LINK MATCH
# =========================
def get_official(text):
    t = text.lower()

    mapping = {
        "НАТО": ["nato"],
        "Минобороны США": ["pentagon", "us defense"],
        "Армия США": ["army"],
        "ВМС США": ["navy"],
        "Корпус морской пехоты США": ["marine"],
        "DARPA": ["darpa"],
        "AFRL": ["air force research"],

        "Rheinmetall": ["rheinmetall"],
        "BAE Systems": ["bae"],
        "Leonardo": ["leonardo"],
        "Saab": ["saab"],
        "Thales": ["thales"],
        "Patria": ["patria"],
        "KNDS": ["knds"],

        "Lockheed Martin": ["lockheed"],
        "Northrop Grumman": ["northrop"],
        "RTX": ["rtx"],
        "General Dynamics": ["general dynamics"],
        "Airbus Defence": ["airbus"],

        "Европейское оборонное агентство": ["eda"]
    }

    for k, keywords in mapping.items():
        if any(w in t for w in keywords):
            return k, OFFICIAL_SOURCES.get(k)

    return None, None


# =========================
# SEND TELEGRAM
# =========================
def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


# =========================
# FETCH NEWS
# =========================
def get_news():
    items = []

    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)

            for e in feed.entries[:5]:

                if not is_recent(e):
                    continue

                title = e.title.lower()

                if any(b in title for b in BLOCK):
                    continue

                if not any(a in title for a in ALLOW):
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

    for n in news:

        if n["link"] in seen:
            continue

        country = detect_country(n["title"])

        title_ru = translate(n["title"])
        title_ru = clean(title_ru)

        org, link = get_official(title_ru)

        extra = ""
        if link:
            extra = f"\n🏛 Официальный источник: {link}"

        msg = f"""{country}

{title_ru}

🔗 {n['link']}{extra}"""

        send(msg)

        print("SENT:", title_ru)

        seen.append(n["link"])

    state["seen"] = seen[-500:]
    save_state(state)


if __name__ == "__main__":
    main()
