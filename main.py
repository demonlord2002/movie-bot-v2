# main.py
import os
import re
import asyncio
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import Message
from utils.database import save_movie, get_movie, list_codes, delete_movie, backup_all
from utils.generator import generate_auto_code
from utils.shortener import short_it
from utils.formatter import format_links_block

load_dotenv("config.env")

API_ID = int(os.getenv("API_ID") or 0)
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID") or 0)
DELETE_TIME = int(os.getenv("DELETE_TIME") or 600)

app = Client("moviebotv2", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

URL_REGEX = re.compile(r"(https?://\S+)")


# ---------- Admin: Attach flow (No auto-post) ----------
@app.on_message(filters.user(ADMIN_ID) & filters.command("attach") & filters.reply)
async def attach_handler(c, m: Message):
    try:
        code = generate_auto_code()
        orig: Message = m.reply_to_message
        if not orig:
            await m.reply_text("❌ Reply to the original post which contains links/text.")
            return

        # Demo video from command args or first t.me link in message
        demo_video = None
        parts = m.text.split(maxsplit=1)
        if len(parts) > 1 and parts[1].startswith("http"):
            demo_video = parts[1].strip()
        else:
            found = URL_REGEX.findall(orig.text or "")
            for u in found:
                if "t.me" in u:
                    demo_video = u
                    break

        # Extract title
        raw_title = (orig.text or "").splitlines()[0][:150] if orig.text else "Unknown"

        # Extract URLs
        link_lines = []
        for line in (orig.text or "").splitlines():
            url_match = URL_REGEX.search(line)
            if url_match:
                url = url_match.group(1).strip()
                label = line[:url_match.start()].strip() or "Download"
                short_url = short_it(url)
                link_lines.append((label, short_url))

        if not link_lines:
            await m.reply_text("❌ No links found in replied message.")
            return

        links_block = format_links_block(link_lines)

        # Save movie
        image_id = orig.photo.file_id if orig.photo else None
        movie_data = {
            "code": code,
            "raw_title": raw_title,
            "links": links_block,
            "demo_video": demo_video or "",
            "image": image_id
        }
        save_movie(code, movie_data)

        await m.reply_text(f"✅ Movie saved successfully.\nCode: {code}\nSubscribers can now DM the bot with this code to get links.")

    except Exception as e:
        await m.reply_text(f"❌ Error: {e}")


# ---------- User DM handler ----------
@app.on_message(filters.private & filters.text)
async def user_dm(c, m: Message):
    code = m.text.strip().upper()
    movie = get_movie(code)
    if not movie:
        await m.reply_text("❌ Invalid code. Check the pinned guide in channel.")
        return

    msg = f"🎬 <b>{movie.get('raw_title','Movie')}</b>\n\n"
    msg += f"📥 <b>Download Links for {movie['code']}</b>\n\n"
    msg += f"{movie['links']}\n\n"

    if movie.get("demo_video"):
        msg += f"🎥 <b>Watch How to Download:</b> <b>{movie.get('demo_video')}</b>\n\n"

    msg += "✅ <b>Click the link you want and wait the download page to load.</b>"

    if movie.get("image"):
        await c.send_photo(
            m.chat.id,
            photo=movie["image"],
            caption=msg,
            disable_web_page_preview=True,
            parse_mode="html"
        )
    else:
        await m.reply_text(msg, disable_web_page_preview=True, parse_mode="html")


if __name__ == "__main__":
    print("✅ MovieBot v2.0 is starting...")
    app.run()
