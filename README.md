# 🖼 Image To Link Bot | Img To URL Bot

ImgBB Telegram Bot — Images ko permanent direct URL mein convert karo!

## ✨ Features
- 📷 **Upload Image** — Photo ya file bhejo → permanent URL
- 🔗 **Upload URL** — URL bhejo → ImgBB pe upload
- ⏰ **Set Expiry** — 1 Hour / 1 Day / 7 Days / 30 Days / Never
- ✏️ **Caption** → Custom filename
- 📋 **Copy Link** — Inline button
- 🔗 **Share Link** — Inline button
- ⏱ **Time Taken** — Upload speed
- 🚫 **18+ Auto-Ban**

---

## 🚀 Local Setup (Without Docker)

```bash
# 1. Clone karo
git clone <your-repo-url>
cd imgbb-bot

# 2. Virtual env banao
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Dependencies install karo
pip install -r requirements.txt

# 4. .env file banao
cp .env.example .env
# .env mein BOT_TOKEN aur IMGBB_KEY dalo

# 5. Bot start karo
python main.py
```

---

## 🐳 Docker Setup

```bash
# 1. .env file banao
cp .env.example .env
# .env mein apna BOT_TOKEN aur IMGBB_KEY dalo

# 2. Docker Compose se run karo
docker-compose up -d

# Logs dekhne ke liye
docker-compose logs -f

# Stop karne ke liye
docker-compose down
```

### Manual Docker Build

```bash
docker build -t imgbb-bot .
docker run -d \
  -e BOT_TOKEN=your_token \
  -e IMGBB_KEY=your_key \
  -p 8080:8080 \
  imgbb-bot
```

---

## ☁️ Cloud Deployment

### Railway
1. GitHub pe push karo
2. Railway mein new project → Deploy from GitHub
3. Environment variables set karo: `BOT_TOKEN`, `IMGBB_KEY`
4. Deploy!

### Render
1. GitHub pe push karo
2. Render mein new Web Service banao
3. Environment variables add karo
4. Start Command: `python main.py`

### Koyeb
1. Docker image build karo aur push karo
2. Koyeb mein deploy karo with env vars

---

## 🔑 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `BOT_TOKEN` | Telegram Bot Token (@BotFather se) | ✅ |
| `IMGBB_KEY` | ImgBB API Key (imgbb.com/api) | ✅ |
| `PORT` | Flask server port (default: 8080) | ❌ |

---

## 📁 Project Structure

```
imgbb-bot/
├── bot.py              # Main bot logic
├── main.py             # Entry point (Flask + Bot)
├── health_server.py    # Flask health check server
├── requirements.txt    # Python dependencies
├── Dockerfile          # Docker image
├── docker-compose.yml  # Docker Compose config
├── .env.example        # Environment variables template
├── .gitignore
└── README.md
```

---

## 📝 Commands

| Command | Description |
|---------|-------------|
| `/start` | Bot start karo |
| `/help` | Help message |
| `/about` | Bot info |

---

## ⚠️ Important Notes
- **18+ content strictly prohibited** — violators auto-banned
- Supported formats: JPG, PNG, BMP, GIF, TIFF, WEBP
- Max file size: 32MB
