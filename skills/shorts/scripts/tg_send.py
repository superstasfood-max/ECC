#!/usr/bin/env python3
"""Send a message or a video to the user's Telegram via their own bot.
Needs TELEGRAM_BOT_TOKEN as a plain environment variable (the token lives in the URL path, so
header-injecting "network secrets" cannot carry it) and api.telegram.org allowed.
Chat id: --chat, $TELEGRAM_CHAT_ID, the latest private chat that messaged the bot (/start; Telegram
keeps those for 24 h), or the last chat used (cached in ~/.cache/shorts/tg_chat_id).
Bot API uploads cap at 50 MB, so larger videos are re-encoded (2-pass) to ~45 MB first.

usage: tg_send.py --text "hello"
       tg_send.py VIDEO.mp4 [--caption "..."] [--chat ID]"""
import json, os, subprocess, sys, tempfile, urllib.parse, urllib.request

LIMIT = 49 * 1024 * 1024
CACHE = os.path.expanduser("~/.cache/shorts/tg_chat_id")  # getUpdates forgets chats after 24 h
TARGET_MB = 45


def api(method, data=None, files=None):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        sys.exit("[tg_send] TELEGRAM_BOT_TOKEN is not set (add it as an environment variable, then start a new session)")
    url = f"https://api.telegram.org/bot{token}/{method}"
    if files:  # multipart via curl keeps this dependency-free and streams large files
        cmd = ["curl", "-sS", "--max-time", "900", url]
        for k, v in (data or {}).items():
            cmd += ["-F", f"{k}={v}"]
        for k, path in files.items():
            cmd += ["-F", f"{k}=@{path};type=video/mp4"]
        out = subprocess.run(cmd, capture_output=True, text=True).stdout
    else:
        body = urllib.parse.urlencode(data or {}).encode()
        out = urllib.request.urlopen(url, body, timeout=60).read().decode()
    res = json.loads(out)
    if not res.get("ok"):
        sys.exit(f"[tg_send] {method} failed: {res.get('description')}")
    return res["result"]


def chat_id(arg):
    if arg:
        return arg
    if os.environ.get("TELEGRAM_CHAT_ID"):
        return os.environ["TELEGRAM_CHAT_ID"]
    for u in reversed(api("getUpdates")):
        chat = (u.get("message") or {}).get("chat", {})
        if chat.get("type") == "private":
            return str(chat["id"])
    if os.path.isfile(CACHE):
        return open(CACHE).read().strip()
    sys.exit("[tg_send] no chat found: open the bot in Telegram and press Start, or pass --chat")


def fit(video):
    if os.path.getsize(video) <= LIMIT:
        return video
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                video], capture_output=True, text=True).stdout)
    vbit = int(TARGET_MB * 8 * 1024 / dur - 192)  # kbit/s, leaving room for 192k audio
    out = os.path.join(tempfile.mkdtemp(), "tg_" + os.path.basename(video))
    log = out + ".log"
    base = ["ffmpeg", "-v", "error", "-y", "-i", video, "-c:v", "libx264", "-preset", "slow", "-b:v", f"{vbit}k",
            "-passlogfile", log]
    subprocess.run(base + ["-pass", "1", "-an", "-f", "null", "/dev/null"], check=True)
    subprocess.run(base + ["-pass", "2", "-maxrate", f"{int(vbit * 1.4)}k", "-bufsize", f"{vbit * 2}k",
                           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out], check=True)
    return out


def main():
    args = sys.argv[1:]
    opt = lambda k: args[args.index(k) + 1] if k in args else None
    chat = chat_id(opt("--chat"))
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    open(CACHE, "w").write(chat)
    if opt("--text"):
        api("sendMessage", {"chat_id": chat, "text": opt("--text")})
        print("[tg_send] message sent")
        return
    video = args[0]
    sent = fit(video)
    probe = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                       "stream=width,height:format=duration", "-of", "json", sent],
                                      capture_output=True, text=True).stdout)
    st, fmt = probe["streams"][0], probe["format"]
    res = api("sendVideo", {"chat_id": chat, "caption": opt("--caption") or "", "supports_streaming": "true",
                            "width": st["width"], "height": st["height"],
                            "duration": int(float(fmt["duration"]))}, {"video": sent})
    size = (res.get("video") or res.get("document") or {}).get("file_size", 0)
    print(f"[tg_send] sent {os.path.basename(video)} ({size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
