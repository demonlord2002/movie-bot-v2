# utils/formatter.py
from html import escape

def make_attractive_comment(code: str, raw_title: str, short_links: str, demo_video: str = None) -> str:
    """
    Build attractive message for admin attach
    """
    demo_part = ""
    if demo_video:
        demo_part = f"\n\n🎥 <b>How to Download (Demo Video)</b>\n🔗 <b>{escape(demo_video)}</b>"

    return (
        f"📦 <b>New Update:</b> <b>{escape(code)}</b>\n"
        f"🎬 <b>Movie:</b> <b>{escape(raw_title)}</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔥 <b>Fast Downloader – Direct Links</b>\n\n"
        f"{short_links}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
        f"{demo_part}\n\n"
        f"📢 <b>Important for Subscribers:</b>\n"
        f"🔥 <b>Use Code:</b> <b>{escape(code)}</b>\n"
        f"🤖 DM the bot with this code to get links"
    )


def format_links_block(link_lines):
    """
    Convert list of (label, url) to fully bold Telegram HTML links block.
    """
    out = []
    for label, url in link_lines:
        out.append(f"👉 <b>{escape(label)}</b>\n🔗 <b>{escape(url)}</b>")
    return "\n\n".join(out)
    
