"""
discord_send.py — Reads a news briefing markdown file and sends it to Discord as embeds.
Called by the Daily News Briefing automation after the agent saves news to a file.

Usage: python "discord_send.py" "path/to/briefing.md"
"""

import sys
import os
import re
import requests
from datetime import datetime

# --- Load .env file if present in script directory or current working directory ---
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

# Section colors for Discord embeds
COLORS = {
    "cybersecurity": 15158332,   # Red
    "stock": 3066993,            # Green
    "market": 3066993,           # Green
    "world": 3447003,            # Blue
    "nepal": 1752220,            # Teal
    "key takeaway": 16776960,    # Yellow
}

def get_color(title: str) -> int:
    title_lower = title.lower()
    for key, color in COLORS.items():
        if key in title_lower:
            return color
    return 3447003  # Default blue

def parse_sections(markdown: str) -> list[dict]:
    """Parse markdown into sections split by ## headings."""
    sections = []
    # Split by ## headings (but not ### subheadings)
    parts = re.split(r'\n(?=## [^#])', markdown)

    for part in parts:
        lines = part.strip().split('\n')
        if not lines:
            continue

        # Find the heading
        heading_match = re.match(r'^## (.+)$', lines[0])
        if not heading_match:
            continue

        title = heading_match.group(1).strip()
        content = '\n'.join(lines[1:]).strip()

        # Trim content to Discord embed description limit (4096 chars)
        if len(content) > 4096:
            content = content[:4090] + "\n..."

        if content:
            sections.append({
                "title": title,
                "content": content,
                "color": get_color(title),
            })

    return sections

def send_embeds(sections: list[dict]):
    """Send sections as Discord embeds, max 10 per message."""
    today = datetime.now().strftime('%B %d, %Y')

    embeds = []
    for section in sections:
        embeds.append({
            "title": section["title"],
            "description": section["content"],
            "color": section["color"],
            "footer": {"text": f"Daily News Briefing — {today}"},
        })

    # Discord allows max 10 embeds per message
    for i in range(0, len(embeds), 10):
        batch = embeds[i:i+10]
        data = {
            "username": BOT_USERNAME,
            "embeds": batch,
        }
        response = requests.post(WEBHOOK_URL, json=data)
        if response.status_code == 204:
            print(f"✅ Sent {len(batch)} embed(s) successfully!")
        else:
            print(f"❌ Failed: {response.status_code} — {response.text}")

def send_plain_text(text: str):
    """Fallback: send as plain text chunks."""
    chunks = []
    current = ""
    for line in text.split('\n'):
        if len(current) + len(line) + 1 > 2000:
            chunks.append(current)
            current = line
        else:
            current += ("\n" if current else "") + line
    if current:
        chunks.append(current)

    for chunk in chunks:
        data = {"content": chunk, "username": BOT_USERNAME}
        response = requests.post(WEBHOOK_URL, json=data)
        if response.status_code == 204:
            print(f"✅ Chunk sent ({len(chunk)} chars)")
        else:
            print(f"❌ Failed: {response.status_code} — {response.text}")

if __name__ == "__main__":
    if not WEBHOOK_URL:
        print("❌ Error: DISCORD_WEBHOOK_URL is not set.")
        print("   Set it in your environment or in a .env file:")
        print("   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...")
        sys.exit(1)

    if len(sys.argv) < 2:
        print("Usage: python discord_send.py <path_to_briefing.md>")
        sys.exit(1)

    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        sys.exit(1)

    with open(filepath, "r", encoding="utf-8") as f:
        markdown = f.read()

    print(f"📰 Parsing briefing from: {filepath}")
    sections = parse_sections(markdown)

    if sections:
        print(f"   Found {len(sections)} sections")
        send_embeds(sections)
    else:
        print("   No sections found, sending as plain text")
        send_plain_text(markdown)
