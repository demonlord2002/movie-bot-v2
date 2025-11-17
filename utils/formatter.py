# utils/formatter.py
from html import escape

def make_attractive_comment(code: str, raw_title: str, short_links: str, demo_video: str = None) -> str:
    """
    Build the attractive, bold, safe message that will be posted as a reply in channel.
    short_links: already-prepared lines with short links + size labels.
    raw_title: can be used for optional non-copyright internal reference - but not required publicly.
    """
    # We will show only title lightly; you can omit title to be safer.
    demo_part = ""
    if demo_video:
        demo_part = f"\n\n🎥 <b>How to Download (Demo Video)</b>\n🔗 {escape(demo_video)}"

    return (
        f"📦 <b>New Update:</b> <b>{escape(code)}</b>\n"
        f"🎬 <b>Movie:</b> <b>{escape(raw_title)}</b>\n"
        f"🎧 <b>Audio:</b> <b>HQ Clean Audio</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔥 <b>Fast Downloader – Direct Links</b>\n\n"
        f"{short_links}\n"
        f"\n━━━━━━━━━━━━━━━━━━━━━━"
        f"{demo_part}\n\n"
        f"📢 <b>Important for Subscribers:</b>\n"
        f"🔥 <b>Use Code:</b> <b>{escape(code)}</b>\n"
        f"🤖 DM the bot with this code to get links"
    )

def format_links_block(link_lines):
    """
    Accepts a list of tuples (label_text, url) and returns the text block where
    each line uses bold labels and the link below as required.
    Example output per item:
    👉 **600MB – 480p**
    🔗 **https://...**
    """
    out = []
    for label, url in link_lines:
        out.append(f"👉 <b>{escape(label)}</b>\n🔗 <b>{escape(url)}</b>\n")
    return "\n".join(out)
  
