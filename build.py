import feedparser, json, os, html
from datetime import datetime
from pytz import timezone
from collections import OrderedDict

# RSS feeds
FEEDS = {
    "Kompas": "https://rss.kompas.com/api/feed/social?apikey=bc58c81819dff4b8d5c53540a2fc7ffd83e6314a",
    "Detik": "https://news.detik.com/berita/rss",
}

# Indonesian weekdays
WEEKDAYS_ID = {
    0: "Senin", 1: "Selasa", 2: "Rabu", 3: "Kamis",
    4: "Jumat", 5: "Sabtu", 6: "Minggu"
}

TZ = timezone("Asia/Jakarta")
NOW = datetime.now(TZ)
TODAY = NOW.date()
DATA_DIR = "headlines"
os.makedirs(DATA_DIR, exist_ok=True)

# ----------------------------------------------------------

def parse_time(entry):
    """Return localized WIB time string like '19:30 WIB'."""
    for field in ("published_parsed", "updated_parsed"):
        if getattr(entry, field, None):
            dt = datetime(*getattr(entry, field)[:6])
            return timezone("UTC").localize(dt).astimezone(TZ).strftime("%H:%M WIB")
    return None

def fetch_today():
    all_items = {}
    for name, url in FEEDS.items():
        feed = feedparser.parse(url)
        items = []
        for e in feed.entries[:20]:
            title = html.escape(e.title)
            link = e.link
            time_str = parse_time(e)
            items.append({"title": title, "link": link, "time": time_str})
        all_items[name] = items
    return all_items

# ----------------------------------------------------------

def save_json(data):
    path = os.path.join(DATA_DIR, f"{TODAY}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_recent(days=3):
    files = sorted(os.listdir(DATA_DIR), reverse=True)
    out = OrderedDict()
    for f in files[:days]:
        date = f.replace(".json", "")
        with open(os.path.join(DATA_DIR, f), encoding="utf-8") as fp:
            out[date] = json.load(fp)
    return out

def indonesian_date(date_str):
    dt = datetime.fromisoformat(date_str)
    return f"{WEEKDAYS_ID[dt.weekday()]}, {dt.strftime('%d-%m-%Y')}"

# ----------------------------------------------------------

def build_html(pages, template):
    content_parts = []
    for date, data in pages.items():
        date_str = indonesian_date(date)
        content_parts.append(f"<h3>{date_str}</h3>")
        for src, items in data.items():
            content_parts.append(f"<h4>[{src}]</h4><ul>")
            for item in items:
                time_html = f" <span class='time'>({item['time']})</span>" if item['time'] else ""
                content_parts.append(
                    f"<li><a href='{item['link']}' target='_blank'>{item['title']}</a>{time_html}</li>"
                )
            content_parts.append("</ul>")
    date_header = indonesian_date(str(TODAY))
    updated = NOW.strftime("%H:%M WIB")
    return (
        template
        .replace("{{DATE}}", date_header)
        .replace("{{UPDATED}}", updated)
        .replace("{{CONTENT}}", "\n".join(content_parts))
    )

# ----------------------------------------------------------

def build_txt(pages):
    lines = []
    for date, data in pages.items():
        date_str = indonesian_date(date)
        lines.append(f"\n{date_str}\n{'=' * len(date_str)}\n")
        for src, items in data.items():
            lines.append(f"\n[{src}]\n")
            for item in items:
                time = f" ({item['time']})" if item['time'] else ""
                lines.append(f"- {item['title']}{time}\n  {item['link']}")
    header = (
        "Berita Hari Ini (Versi TXT)\n"
        f"{indonesian_date(str(TODAY))}\n"
        f"Terakhir diperbarui: {NOW.strftime('%H:%M WIB')}\n"
        + "=" * 40 + "\n"
    )
    footer = "\n\nHalaman ini diperbarui otomatis setiap ±10 menit.\nSumber: Kompas.com & Detik.com\n"
    return header + "\n".join(lines) + footer

# ----------------------------------------------------------

def main():
    data = fetch_today()
    save_json(data)

    recent = load_recent(3)
    template = open("template.html", encoding="utf-8").read()

    open("index.html", "w", encoding="utf-8").write(build_html(recent, template))
    open("berita.txt", "w", encoding="utf-8").write(build_txt(recent))

    all_days = sorted(os.listdir(DATA_DIR), reverse=True)
    if len(all_days) > 3:
        older = OrderedDict()
        for f in all_days[3:]:
            date = f.replace(".json", "")
            with open(os.path.join(DATA_DIR, f), encoding="utf-8") as fp:
                older[date] = json.load(fp)
        page2_html = build_html(older, template.replace("Versi TXT", "Arsip"))
        open("page2.html", "w", encoding="utf-8").write(page2_html)

    print("✅ Berita Hari Ini updated — HTML + TXT generated.")

if __name__ == "__main__":
    main()
