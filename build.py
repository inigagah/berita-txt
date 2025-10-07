import feedparser, json, os, html
from datetime import datetime
from pytz import timezone
from collections import OrderedDict

# ------------------ Config ------------------
FEEDS = {
    "Kompas": "https://rss.kompas.com/api/feed/social?apikey=bc58c81819dff4b8d5c53540a2fc7ffd83e6314a",
    "Detik": "https://news.detik.com/berita/rss",
    # Add more here anytime
}

# How many most-recent days to show on the front page
DAYS_ON_FRONT = 3

# Timezone
TZ = timezone("Asia/Jakarta")
NOW = datetime.now(TZ)
TODAY = NOW.date()

DATA_DIR = "headlines"
os.makedirs(DATA_DIR, exist_ok=True)

WEEKDAYS_ID = {
    0: "Senin", 1: "Selasa", 2: "Rabu", 3: "Kamis",
    4: "Jumat", 5: "Sabtu", 6: "Minggu"
}
# --------------------------------------------

def parse_datetime_wib(entry):
    """
    Returns a timezone-aware datetime in WIB if the entry has a valid
    published/updated time; otherwise returns None.
    """
    # feedparser gives struct_time in UTC if timezone is known
    st = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if not st:
        return None
    # build a naive datetime from struct_time
    dt_utc_naive = datetime(*st[:6])
    # assume UTC for safety, then convert to WIB
    from pytz import utc
    dt_wib = utc.localize(dt_utc_naive).astimezone(TZ)
    return dt_wib

def fetch_today_only():
    """
    Fetch top items from each feed, but KEEP ONLY entries whose WIB date == TODAY.
    """
    all_items = {}
    for name, url in FEEDS.items():
        feed = feedparser.parse(url)
        items = []
        for e in feed.entries:
            dt = parse_datetime_wib(e)
            if not dt:
                continue  # skip if no reliable time
            if dt.date() != TODAY:
                continue  # strict: only today's WIB items
            items.append({
                "title": html.escape(e.title),
                "link": e.link,
                "time": dt.strftime("%H:%M WIB"),
            })
        # Sort newest-first just in case
        items.sort(key=lambda x: x["time"], reverse=True)
        all_items[name] = items
    return all_items

def save_json_for_today(data):
    path = os.path.join(DATA_DIR, f"{TODAY}.json")
    # Load previous data if exists
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            prev = json.load(f)
        # Merge: keep all old items, add new ones, avoid duplicates by link
        for src, items in data.items():
            old_items = prev.get(src, [])
            # Use link as unique key
            links = {it["link"] for it in items}
            for it in old_items:
                if it["link"] not in links:
                    items.append(it)
            # Sort newest first by time (if available)
            items.sort(key=lambda x: x.get("time", ""), reverse=True)
            data[src] = items
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_recent(days):
    files = [f for f in os.listdir(DATA_DIR) if f.endswith(".json")]
    files.sort(reverse=True)  # newest first
    out = OrderedDict()
    for f in files[:days]:
        date_str = f[:-5]  # strip .json
        with open(os.path.join(DATA_DIR, f), encoding="utf-8") as fp:
            out[date_str] = json.load(fp)
    return out

def indonesian_date(date_str):
    dt = datetime.fromisoformat(date_str)
    return f"{WEEKDAYS_ID[dt.weekday()]}, {dt.strftime('%d-%m-%Y')}"

def build_html_from_pages(pages):
    parts = []
    for date, data in pages.items():
        date_str = indonesian_date(date)
        parts.append(f"<h3>{date_str}</h3>")
        for src, items in data.items():
            if not items:
                continue
            parts.append(f"<h4>[{src}]</h4><ul>")
            for it in items:
                t = f" <span class='time'>({it['time']})</span>" if it.get("time") else ""
                parts.append(f"<li><a href='{it['link']}' target='_blank'>{it['title']}</a>{t}</li>")
            parts.append("</ul>")
    return "\n".join(parts) if parts else "<p class='empty'>Belum ada headline untuk rentang ini.</p>"

def render_template(content, title_suffix="Versi TXT"):
    # We keep the same header; date shows "today" and updated time is NOW
    date_header = indonesian_date(str(TODAY))
    updated = NOW.strftime("%H:%M WIB")
    with open("template.html", encoding="utf-8") as f:
        tpl = f.read()
    return (
        tpl
        .replace("{{DATE}}", date_header)
        .replace("{{UPDATED}}", updated)
        .replace("{{CONTENT}}", content)
    )

def build_front_and_archive():
    # FRONT: last N days
    recent = load_recent(DAYS_ON_FRONT)
    index_html = render_template(build_html_from_pages(recent))
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(index_html)

    # ARCHIVE: everything older than front
    files = [f for f in os.listdir(DATA_DIR) if f.endswith(".json")]
    files.sort(reverse=True)
    older_files = files[DAYS_ON_FRONT:]  # older than front window

    if older_files:
        older = OrderedDict()
        for f in older_files:
            date_str = f[:-5]
            with open(os.path.join(DATA_DIR, f), encoding="utf-8") as fp:
                older[date_str] = json.load(fp)
        page2_html = render_template(build_html_from_pages(older), title_suffix="Arsip")
    else:
        # Always write page2.html so the file exists even if empty
        empty_msg = "<p class='empty'>Belum ada arsip yang lebih lama dari hari-hari di halaman utama.</p>"
        page2_html = render_template(empty_msg, title_suffix="Arsip")

    with open("page2.html", "w", encoding="utf-8") as f:
        f.write(page2_html)

def build_txt(pages):
    lines = []
    for date, data in pages.items():
        date_str = indonesian_date(date)
        lines.append(f"\n{date_str}\n{'=' * len(date_str)}\n")
        for src, items in data.items():
            if not items:
                continue
            lines.append(f"\n[{src}]\n")
            for it in items:
                t = f" ({it['time']})" if it.get("time") else ""
                lines.append(f"- {it['title']}{t}\n  {it['link']}")
    header = (
        "Berita Hari Ini (Versi TXT)\n"
        f"{indonesian_date(str(TODAY))}\n"
        f"Terakhir diperbarui: {NOW.strftime('%H:%M WIB')}\n"
        + "=" * 40 + "\n"
    )
    footer = "\n\nHalaman ini diperbarui otomatis setiap ±10 menit.\nSumber: Kompas.com & Detik.com\n"
    return header + "\n".join(lines) + footer

def main():
    today_data = fetch_today_only()   # <-- strict filtering by TODAY in WIB
    save_json_for_today(today_data)

    # Build front and archive HTML
    build_front_and_archive()

    # Build TXT for the last N days
    recent = load_recent(DAYS_ON_FRONT)
    txt_out = build_txt(recent)
    with open("berita.txt", "w", encoding="utf-8") as f:
        f.write(txt_out)

    print("✅ Built: index.html, page2.html, berita.txt, and saved today's JSON.")

if __name__ == "__main__":
    main()
