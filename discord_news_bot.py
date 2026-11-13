"""
discord_news_bot.py — Sends the Daily News Briefing to a Discord channel via webhook.

Usage:
  1. Set DISCORD_WEBHOOK_URL in .env or as an environment variable
  2. Run: python discord_news_bot.py
"""

import os
import sys
import requests
from datetime import datetime

# --- Load .env file if present ---
def load_env_file():
    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"),
        os.path.join(os.getcwd(), ".env"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, val = line.split("=", 1)
                            os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))
                break
            except Exception:
                pass

load_env_file()

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
BOT_USERNAME = "📰 Daily News Briefing"

def send_discord_message(content: str, webhook_url: str = WEBHOOK_URL):
    """Send a plain text message to Discord via webhook."""
    chunks = split_into_chunks(content, 2000)
    for chunk in chunks:
        data = {
            "content": chunk,
            "username": BOT_USERNAME,
        }
        response = requests.post(webhook_url, json=data)
        if response.status_code == 204:
            print(f"✅ Chunk sent successfully ({len(chunk)} chars)")
        else:
            print(f"❌ Failed: {response.status_code} — {response.text}")

def send_discord_embeds(sections: list[dict], webhook_url: str = WEBHOOK_URL):
    """
    Send rich embeds to Discord — one embed per news section.
    Each section dict: {"title": str, "content": str, "color": int}
    """
    embeds = []
    for section in sections:
        embeds.append({
            "title": section["title"],
            "description": section["content"][:4096],
            "color": section.get("color", 3447003),
            "footer": {"text": f"Daily News Briefing — {datetime.now().strftime('%B %d, %Y')}"},
        })

    data = {
        "username": BOT_USERNAME,
        "embeds": embeds[:10],
    }
    response = requests.post(webhook_url, json=data)
    if response.status_code == 204:
        print("✅ Embeds sent successfully!")
    else:
        print(f"❌ Failed: {response.status_code} — {response.text}")

def split_into_chunks(text: str, max_len: int = 2000) -> list[str]:
    """Split text into chunks at line boundaries."""
    lines = text.split("\n")
    chunks = []
    current = ""
    for line in lines:
        if len(current) + len(line) + 1 > max_len:
            chunks.append(current)
            current = line
        else:
            current += ("\n" if current else "") + line
    if current:
        chunks.append(current)
    return chunks

def build_news_sections() -> list[dict]:
    """Sample sections template."""
    return [
        {
            "title": "🔒 Cybersecurity",
            "color": 15158332,
            "content": (
                "• **Sample Vulnerability Alert** — Threat actors actively exploiting zero-day flaw | [Source](https://example.com)\n"
                "• **Patch Tuesday Highlights** — Critical security updates released | [Source](https://example.com)"
            ),
        },
        {
            "title": "📈 Stock Market",
            "color": 3066993,
            "content": (
                "**Market Snapshot**\n"
                "S&P 500: 7,592 | Dow: 52,297 | NASDAQ: 25,366\n\n"
                "• **Tech Movers** — Semiconductor and AI stocks drive session volatility | [Source](https://example.com)"
            ),
        },
        {
            "title": "🌍 World News",
            "color": 3447003,
            "content": (
                "• **Global Diplomatic Summits** — International leaders convene on climate and security | [Source](https://example.com)"
            ),
        },
        {
            "title": "🇳🇵 Nepal News",
            "color": 1752220,
            "content": (
                "• **Himalayan Climate Advocacy** — Delegation presents climate adaptation priorities | [Source](https://example.com)"
            ),
        },
    ]

if __name__ == "__main__":
    if not WEBHOOK_URL:
        print("⚠️  Please set your Discord webhook URL!")
        print("   Set DISCORD_WEBHOOK_URL in .env or as an environment variable.")
        sys.exit(1)

    print(f"📰 Sending sample news briefing to Discord...")
    sections = build_news_sections()
    send_discord_embeds(sections)
