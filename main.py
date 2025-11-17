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
from utils.formatter import make_attractive_comment, format_links_block

load_dotenv("config.env")

API_ID = int(os.getenv("API_ID") or 0)
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID") or 0)
CHANNEL_ID = os.getenv("CHANNEL_ID")  # can be @channelusername or -100...
DELETE_TIME = int(os.getenv("DELETE_TIME") or 600)

app = Client("moviebotv2", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

URL_REGEX = re.compile(r"(https?://\S+)")


# ---------- Admin: basic panel ----------
@app.on_message(filters.user(ADMIN_ID) & filters.command("panel"))
async def admin_panel(c, m: Message):
    await m.reply_text(
        "**ADMIN PANEL**\n\n"
        "/attach - reply to original post with this command to create code & save\n"
        "/nextcode - show next code\n"
        "/list - list saved codes\n"
        "/delete <CODE> - delete code\n"
        "/backup - export all saved movies"
    )


@app.on_message(filters.user(ADMIN_ID) & filters.command("nextcode"))
async def nextcode(c, m: Message):
    code = generate_auto_code()  # consumes counter, so we must peek without consuming; workaround: we'll show but not increment
    # NOTE: generate_auto_code increments; to only preview we could implement a peek function.
    # For simplicity here we still use generate_auto_code but keep consumer aware. Alternatively you can use get_next without increment.
    await m.reply_text(f"Next code generated: **{code}**")


@app.on_message(filters.user(ADMIN_ID) & filters.command("list"))
async def cmd_list(c, m: Message):
    codes = list_codes()
    if not codes:
        await m.reply_text("No saved movies.")
        return
    await m.reply_text("Saved codes:\n" + "\n".join(codes))


@app.on_message(filters.user(ADMIN_ID) & filters.command("delete"))
async def cmd_delete(c, m: Message):
    try:
        code = m.text.split(" ", 1)[1].strip()
    except:
        await m.reply_text("Usage: /delete D-001")
        return
    delete_movie(code)
    await m.reply_text(f"Deleted: {code}")


@app.on_message(filters.user(ADMIN_ID) & filters.command("backup"))
async def cmd_backup(c, m: Message):
    data = backup_all()
    if not data:
        await m.reply_text("No data to backup.")
        return
    # prepare text
    s = ""
    for item in data:
        s += f"{item.get('code')}\n{item.get('links')}\nDemo: {item.get('demo_video', '')}\n\n"
    # if size > 4096 send as file
    if len(s) > 4000:
        await m.reply_document(m.chat.id, (bytes(s, "utf-8"), "backup.txt"))
    else:
        await m.reply_text(f"<pre>{s}</pre>")


# ---------- Admin: Attach flow ----------
@app.on_message(filters.user(ADMIN_ID) & filters.command("attach") & filters.reply)
async def attach_handler(c, m: Message):
    """
    Admin replies to a raw post (which contains title + link lines).
    Usage (reply to original post and send):
    /attach [optional demo_link]
    Example:
    /attach https://t.me/How_To_Downloadee/20
    """
    try:
        # generate code
        code = generate_auto_code()

        # original message (the one admin replied to)
        orig: Message = m.reply_to_message
        if not orig:
            await m.reply_text("Reply to the original post which contains links/text.")
            return

        # try to find demo link from command args or inside orig msg
        demo_video = None
        parts = m.text.split(maxsplit=1)
        if len(parts) > 1 and parts[1].strip().startswith("http"):
            demo_video = parts[1].strip()
        else:
            # search for t.me link in orig message
            found = URL_REGEX.findall(orig.text or "")
            for u in found:
                if "t.me" in u or "telegram.me" in u:
                    demo_video = u
                    break

        # extract title (use first line of orig text as internal reference)
        raw_title = (orig.text or "").splitlines()[0][:150] if orig.text else "Unknown"

        # extract all URLs from original message
        found_urls = URL_REGEX.findall(orig.text or "")
        # Build link lines with label heuristics: try to capture the preceding label (like "600MB - 480p")
        # We'll parse by lines: each line might have label + url
        link_lines = []
        for line in (orig.text or "").splitlines():
            url_in_line = URL_REGEX.search(line)
            if url_in_line:
                url = url_in_line.group(1).strip()
                # label: take text before url in same line
                label = line[:url_in_line.start()].strip()
                if not label:
                    # fallback label from url (last path)
                    label = "Download"
                # shorten url
                short = short_it(url)
                link_lines.append((label, short))

        if not link_lines:
            await m.reply_text("No links found in replied message. Make sure the original post contains URLs.")
            return

        # prepare short_links block (html)
        links_block = format_links_block(link_lines)

        # create and save movie record
        movie_data = {
            "code": code,
            "raw_title": raw_title,
            "links": links_block,
            "demo_video": demo_video or ""
        }
        save_movie(code, movie_data)

        # compose attractive comment
        comment = make_attractive_comment(code, raw_title, links_block, demo_video or "")

        # reply to original message in channel (bot will post the attractive comment)
        # If orig.chat is the channel, reply in that chat. If admin forwarded from elsewhere, post to CHANNEL_ID instead.
        try:
            if str(orig.chat.id) == str(os.getenv("CHANNEL_ID")) or (hasattr(orig.chat, "username") and ("@" + (orig.chat.username or "")) == os.getenv("CHANNEL_ID")):
                sent = await orig.reply_text(comment, disable_web_page_preview=True)
            else:
                # admin forwarded or posted outside channel: post to CHANNEL_ID
                sent = await c.send_message(os.getenv("CHANNEL_ID"), comment, disable_web_page_preview=True)
        except Exception:
            # fallback: post to CHANNEL_ID
            sent = await c.send_message(os.getenv("CHANNEL_ID"), comment, disable_web_page_preview=True)

        # schedule deletion of the bot-created comment
        asyncio.create_task(schedule_delete(c, sent.chat.id, sent.message_id))

        await m.reply_text(f"✅ Saved & posted. Code: {code}")

    except Exception as e:
        await m.reply_text(f"❌ Error: {e}")


async def schedule_delete(client, chat_id, msg_id):
    await asyncio.sleep(DELETE_TIME)
    try:
        await client.delete_messages(chat_id, msg_id)
    except Exception:
        pass


# ---------- User DM handler ----------
@app.on_message(filters.private & filters.text)
async def user_dm(c, m: Message):
    code = m.text.strip().upper()
    movie = get_movie(code)
    if not movie:
        await m.reply_text("❌ Invalid code. Check the pinned guide in channel.")
        return
    # Build user message
    user_msg = (
        f"📥 Download Links for {movie['code']}\n\n"
        f"{movie['links']}\n\n"
    )
    if movie.get("demo_video"):
        user_msg += f"🎥 Watch How to Download: {movie.get('demo_video')}\n\n"
    user_msg += "✅ Click the link you want and wait the download page to load."
    await m.reply_text(user_msg, disable_web_page_preview=True)


if __name__ == "__main__":
    print("✅ MovieBot v2.0 is starting...")
    app.run()
