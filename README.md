# 🔴 Wasi-Tube Downloader — Setup Guide

## ⚡ Ek Baar Setup — Phir Zindagi Bhar Use Karo!

---

## 📋 Zarooriyat (Requirements)

| Tool     | Kaise Install karein |
|----------|---------------------|
| Python 3 | https://python.org/downloads |
| ffmpeg   | Neeche dekho |
| pip      | Python ke saath aata hai |

---

## 🚀 Step-by-Step Setup

### Step 1 — Folder Extract Karo
```
wasi-tube/
├── server.py
├── requirements.txt
├── static/
│   └── index.html
└── downloads/      ← Automatically banta hai
```

### Step 2 — Libraries Install Karo
```bash
pip install flask flask-cors yt-dlp
```

### Step 3 — ffmpeg Install Karo

**Windows:**
1. https://ffmpeg.org/download.html se download karo
2. ZIP extract karo → bin/ffmpeg.exe ko C:\ffmpeg\bin mein rakho
3. System PATH mein add karo
   - Search: "Environment Variables"
   - Path → Edit → New → `C:\ffmpeg\bin`

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt install ffmpeg
```

### Step 4 — Server Chalao
```bash
cd wasi-tube
python server.py
```

### Step 5 — Browser Mein Kholo
```
http://localhost:5000
```

---

## 🎮 Use Karna

1. **URL copy karo** — YouTube / Instagram / Facebook / TikTok
2. **Paste karo** input mein
3. **Format choose karo** — 1080p / 720p / 480p / MP3
4. **ANALYZE** button dabao
5. **DOWNLOAD** button dabao
6. **"File Save Karein"** button se file download karo

Downloaded files: `wasi-tube/downloads/` folder mein mileingi

---

## ❓ Common Masle

| Masla | Hal |
|-------|-----|
| `yt-dlp not found` | `pip install yt-dlp` chalao |
| `ffmpeg not found` | ffmpeg install karo (Step 3) |
| Instagram kaam nahi kar raha | Login cookies ki zaroorat ho sakti hai |
| TikTok error | URL dobara copy karo (share button se) |

---

## 📁 Supported Formats

- 🎬 **1080p** — Full HD MP4
- 🎥 **720p** — HD MP4  
- 📹 **480p** — Standard MP4
- 🎵 **MP3** — Audio Only (High Quality)

## 🌐 Supported Platforms

- ▶ YouTube
- ◈ Instagram (Reels, Posts)
- ƒ Facebook (Videos)
- ♪ TikTok

---

*Made with ❤️ by Wasi*
