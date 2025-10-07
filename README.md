# 📰 Berita Hari Ini (Versi TXT)

A hyper-minimal, automatically updating daily news feed powered by [Kompas](https://www.kompas.com/) and [Detik](https://www.detik.com/) RSS — displayed in a terminal-style **Courier** layout with the **Dracula color scheme**.

Each headline includes its publish time (in WIB), and the front page keeps the **latest 3 days** of news.  
Older entries are automatically moved to `page2.html` as an archive.

---

## ✨ Features

- 🕐 **Auto-updating** every 10 minutes via GitHub Actions  
- 📰 **Headlines from Kompas & Detik** (RSS feeds)  
- 💾 **Local JSON storage** for each day (`/headlines/YYYY-MM-DD.json`)  
- 🧱 **Hyper-minimal design** using Courier font  
- 🌒 **Dracula color palette** (dark terminal look)  
- 📅 **Timestamp** per headline (in WIB)  
- 📜 **Plain text version** (`berita.txt`) generated alongside HTML  
- 📂 **Auto-archiving** of older headlines to `page2.html`
