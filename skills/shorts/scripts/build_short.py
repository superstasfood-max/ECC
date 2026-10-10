#!/usr/bin/env python3
"""Build a vertical Short from one talking-head take, driven by a project JSON:
hook, speaker-driven crops, choice cards (photo or icon) with winner reveal + chime,
top karaoke subtitles, mono audio, blurred subscribe/like ending with SFX.

usage: build_short.py PROJECT.json SRC OUT.mp4 [--preview] [--grade]
  --preview  540x960 small file for review (CRF 30)
  --grade    warm/punchy colour grade (cards and subtitles are not graded)
Asset dirs (relative to the project file): icons/ (Fluent 3D PNGs), photos/ (<item>.jpg).
"""
import json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else None
P = json.load(open(PROJECT)) if PROJECT else {}
BASE = os.path.dirname(PROJECT) if PROJECT else SCRIPTS
W, H, FPS = (P.get("canvas", {}).get(k, d) for k, d in (("width", 1080), ("height", 1920), ("fps", 30)))
FONT = P.get("font", "/usr/share/fonts/opentype/inter/Inter-Black.otf")
FONT_DIR = os.path.dirname(FONT)
ICONS = os.path.join(BASE, P.get("icons_dir", "icons"))
PHOTOS = os.path.join(BASE, P.get("photos_dir", "photos"))
ITEMS = P.get("items", {})
FRAME = {k: tuple(v) for k, v in P.get("framing", {}).items()}
SHOTS = [(s["in"], s["out"], s["frame"], s.get("hook", False)) for s in P.get("shots", [])]
CTA_CFG = P.get("cta", {})
CTA = (CTA_CFG.get("in", 0), CTA_CFG.get("out", 0))
CARDS = [(c["show"], c.get("win_at"), c["hide"], c["left"], c["right"], c.get("winner"))
         for c in P.get("cards", [])]
SUBS = [(s["in"], s["out"], s["text"]) for s in P.get("subs", [])]
MONO = P.get("audio", {}).get("mono_channel", "c0")


def occurrences(t, hook=None):
    """All output times where source time t is on screen (optionally hook-only/main-only)."""
    out, acc = [], 0.0
    for a, b, _, is_hook in SHOTS:
        if a <= t <= b and (hook is None or hook == is_hook):
            out.append(acc + t - a)
        acc += b - a
    return out


def main_time(t):
    """Output time for a source time in the main edit; clamps into the next kept shot."""
    acc, best = 0.0, None
    for a, b, _, is_hook in SHOTS:
        if not is_hook:
            if a <= t <= b:
                return acc + t - a
            if t < a and best is None:
                best = acc
        acc += b - a
    return best if best is not None else acc


def main_len():
    return sum(b - a for a, b, _, _ in SHOTS)


def rounded(img, r):
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, img.size[0] - 1, img.size[1] - 1), r, fill=255)
    img.putalpha(m)
    return img


def food_tile(name, size):
    p = os.path.join(PHOTOS, ITEMS[name].get("photo", ""))
    if os.path.isfile(p):
        im = ImageOps.fit(Image.open(p).convert("RGB"), (size, size), Image.LANCZOS)
        return rounded(im.convert("RGBA"), 34)
    icon = Image.open(os.path.join(ICONS, ITEMS[name]["icon"] + "_3d.png")).convert("RGBA")
    tile = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    tile.alpha_composite(icon.resize((int(size * .8),) * 2, Image.LANCZOS), (int(size * .1),) * 2)
    return tile


def card_png(left, right, winner, path):
    img = Image.new("RGBA", (W, 560), (0, 0, 0, 0))
    vs = ImageFont.truetype(FONT, 60)
    for k, name in enumerate((left, right)):
        x0 = 60 + k * 560
        won, lost = winner == name, winner is not None and winner != name
        box = Image.new("RGBA", (400, 470), (0, 0, 0, 0))
        d = ImageDraw.Draw(box)
        d.rounded_rectangle((0, 0, 399, 469), 44, fill=(20, 120, 60, 240) if won else (22, 22, 26, 225),
                            outline=(255, 214, 0, 255) if won else (255, 255, 255, 110),
                            width=10 if won else 3)
        box.alpha_composite(food_tile(name, 352), (24, 24))
        size = 50
        while ImageDraw.Draw(box).textlength(name.upper(), font=ImageFont.truetype(FONT, size)) > 360:
            size -= 2
        d.text((200, 420), name.upper(), font=ImageFont.truetype(FONT, size), anchor="mm",
               fill="white", stroke_width=3, stroke_fill="black")
        if won:
            d.ellipse((312, 6, 392, 86), fill=(255, 214, 0, 255), outline=(20, 20, 20), width=4)
            d.line([(332, 46), (348, 62), (374, 30)], fill=(20, 20, 20), width=10)
        if lost:
            gray = box.convert("LA").convert("RGBA")
            box = Image.blend(Image.new("RGBA", box.size, (0, 0, 0, 0)), gray, 0.55)
        shadow = Image.new("RGBA", (440, 510), (0, 0, 0, 0))
        ImageDraw.Draw(shadow).rounded_rectangle((20, 26, 420, 496), 44, fill=(0, 0, 0, 150))
        img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(14)), (x0 - 20, 30))
        img.alpha_composite(box, (x0, 40))
    d = ImageDraw.Draw(img)
    d.ellipse((W / 2 - 66, 209, W / 2 + 66, 341), fill=(230, 40, 40, 255), outline="white", width=6)
    d.text((W / 2, 275), "VS", font=vs, anchor="mm", fill="white")
    img.save(path)


def cta_png(path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    big = ImageFont.truetype(FONT, 76)
    d.text((W / 2, 640), CTA_CFG.get("title", "ПОНРАВИЛОСЬ?"), font=big, anchor="mm", fill="white",
           stroke_width=6, stroke_fill="black")
    # subscribe button
    d.rounded_rectangle((150, 760, 930, 930), 85, fill=(230, 33, 23, 255))
    bell = Image.open(os.path.join(ICONS, "bell_3d.png")).convert("RGBA").resize((120, 120))
    img.alpha_composite(bell, (190, 785))
    d.text((590, 846), CTA_CFG.get("subscribe", "ПОДПИШИСЬ"), font=ImageFont.truetype(FONT, 66), anchor="mm", fill="white")
    # like button
    d.rounded_rectangle((150, 990, 930, 1160), 85, fill=(255, 255, 255, 255))
    thumb = Image.open(os.path.join(ICONS, "thumbs_up_3d.png")).convert("RGBA").resize((120, 120))
    img.alpha_composite(thumb, (190, 1015))
    d.text((590, 1076), CTA_CFG.get("like", "СТАВЬ ЛАЙК"), font=ImageFont.truetype(FONT, 66), anchor="mm", fill=(20, 20, 20))
    img.save(path)


def ass_time(t):
    cs = int(round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def write_ass(path):
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Inter Black,68,&H0000D7FF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,0,0,1,6,3,8,80,80,250,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    for s, e, text in SUBS:
        for a in occurrences(s):  # hook repeats its lines
            b = a + (e - s)
            words = text.split()
            chunks = [words[i:i + 3] for i in range(0, len(words), 3)]
            if len(chunks) > 1 and len(chunks[-1]) == 1:
                tail = chunks.pop()
                chunks[-1] += tail
            total = sum(len(w) + 1 for w in words)
            t = a
            for ch in chunks:
                dur = (b - a) * sum(len(w) + 1 for w in ch) / total
                n = sum(len(x) + 1 for x in ch)
                ks = "".join(f"{{\\k{max(1, int(dur * 100 * (len(w) + 1) / n))}}}{w} " for w in ch)
                pop = r"{\fscx75\fscy75\t(0,90,\fscx100\fscy100)}"
                lines.append(f"Dialogue: 0,{ass_time(t)},{ass_time(t + dur)},Cap,,0,0,0,,{pop}{ks.strip().upper()}")
                t += dur
    open(path, "w").write(head + "\n".join(lines) + "\n")


def main():
    src, out = sys.argv[2], sys.argv[3]
    preview = "--preview" in sys.argv
    # warm, punchy restaurant look: gentle S-curve, a touch more colour, soft vignette
    grade = (",curves=all='0/0 0.25/0.22 0.5/0.52 0.75/0.8 1/1',"
             "eq=saturation=1.14:contrast=1.04,colorbalance=rs=-0.03:bs=0.04:rh=0.04:bh=-0.03,"
             "vignette=angle=PI/5") if "--grade" in sys.argv else ""
    tmp = os.path.join(BASE, "build")
    os.makedirs(tmp, exist_ok=True)
    subprocess.run([sys.executable, os.path.join(SCRIPTS, "choice_sfx.py"), os.path.join(tmp, "choice.wav")], check=True)
    subprocess.run([sys.executable, os.path.join(SCRIPTS, "cta_sfx.py"), os.path.join(tmp, "sfx.wav"),
                    f"{max(CTA[1] - CTA[0], 1.5):.2f}"], check=True)
    write_ass(os.path.join(tmp, "subs.ass"))
    mono = f"pan=stereo|c0={MONO}|c1={MONO}"  # camera's two mics disagree; use the cleaner left one

    inputs, g, cat = [], [], ""
    for k, (a, b, fr, _) in enumerate(SHOTS):
        z, cx, cy = FRAME[fr]
        cw, chh = W / z, H / z
        x0 = min(max(cx * W - cw / 2, 0), W - cw)
        y0 = min(max(cy * H - chh / 2, 0), H - chh)
        inputs += ["-ss", f"{a:.3f}", "-t", f"{b - a + 0.3:.3f}", "-i", src]
        # crop in source pixels (fractions of the frame) so close-ups keep full resolution
        g.append(f"[{k}:v]crop=iw/{z}:ih/{z}:iw*{x0 / W:.4f}:ih*{y0 / H:.4f},"
                 f"scale={W}:{H}:flags=lanczos{grade},"
                 f"setsar=1,fps={FPS},trim=duration={b - a:.3f},setpts=PTS-STARTPTS[v{k}]")
        g.append(f"[{k}:a]{mono},aresample=48000,atrim=duration={b - a:.3f},asetpts=PTS-STARTPTS,"
                 f"afade=t=in:d=0.015,afade=t=out:st={b - a - 0.02:.3f}:d=0.02[a{k}]")
        cat += f"[v{k}][a{k}]"
    # blurred ending under the call to action
    k = len(SHOTS)
    a, b = CTA
    d = b - a
    inputs += ["-ss", f"{a:.3f}", "-t", f"{d + 0.3:.3f}", "-i", src]
    g.append(f"[{k}:v]scale={W}:{H}:flags=lanczos{grade},setsar=1,fps={FPS},trim=duration={d:.3f},setpts=PTS-STARTPTS,"
             f"split[cs][cb]")
    g.append("[cb]gblur=sigma=28,eq=brightness=-0.12,format=rgba,fade=t=in:st=0:d=0.45:alpha=1[cbl]")
    g.append(f"[cs][cbl]overlay=0:0[v{k}]")
    g.append(f"[{k}:a]{mono},aresample=48000,atrim=duration={d:.3f},asetpts=PTS-STARTPTS,"
             f"afade=t=out:st=0:d=0.3[a{k}]")
    cat += f"[v{k}][a{k}]"
    n = k + 1
    g.append(f"{cat}concat=n={n}:v=1:a=1[base][araw]")
    last, idx = "base", n
    end_main = main_len()

    def overlay_png(png, t0, t1, x, y, fin=True, fout=True, rise=0):
        nonlocal last, idx
        inputs.extend(["-loop", "1", "-t", f"{t1 - t0:.3f}", "-i", png])
        f = (f"fade=t=in:st=0:d=0.18:alpha=1," if fin else "") + \
            (f"fade=t=out:st={t1 - t0 - 0.15:.3f}:d=0.15:alpha=1," if fout else "")
        g.append(f"[{idx}:v]format=rgba,{f}setpts=PTS+{t0:.3f}/TB[c{idx}]")
        yy = f"{y}+{rise}*max(0\\,1-(t-{t0:.3f})/0.3)" if rise else str(y)
        g.append(f"[{last}][c{idx}]overlay={x}:'{yy}':eof_action=pass:"
                 f"enable='between(t,{t0:.3f},{t1:.3f})'[o{idx}]")
        last, idx = f"o{idx}", idx + 1

    for c, (show, win, hide, l, r, wname) in enumerate(CARDS):
        states = [(show, win if win else hide, None)] + ([(win, hide, wname)] if win else [])
        for s_i, (s0, s1, w) in enumerate(states):
            t0, t1 = main_time(s0), main_time(s1)
            if s1 == hide and hide >= SHOTS[-1][1]:
                t1 = end_main
            if t1 - t0 < 0.05:
                continue
            png = os.path.join(tmp, f"card{c}_{s_i}.png")
            card_png(l, r, w, png)
            sc = Image.open(png)
            sc.resize((int(sc.width * .76), int(sc.height * .76)), Image.LANCZOS).save(png)
            overlay_png(png, t0, t1, int(W * .12), 1250, fin=s_i == 0, fout=s1 == hide,
                        rise=40 if s_i == 0 else 0)
    cta = os.path.join(tmp, "cta.png")
    cta_png(cta)
    overlay_png(cta, end_main + 0.25, end_main + d, 0, 0, fout=False, rise=60)

    sub = os.path.join(tmp, "subs.ass").replace(":", r"\:")
    fin_scale = ",scale=540:960" if preview else ""
    g.append(f"[{last}]subtitles='{sub}':fontsdir={FONT_DIR}{fin_scale},format=yuv420p[v]")
    inputs.extend(["-i", os.path.join(tmp, "sfx.wav")])
    g.append("[araw]highpass=f=80,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[an]")
    ms = int(end_main * 1000)
    g.append(f"[{idx}:a]aresample=48000,pan=stereo|c0=c0|c1=c0,adelay={ms}|{ms}[sfx]")
    wins = [main_time(c[1]) for c in CARDS if c[1]]
    inputs.extend(["-i", os.path.join(tmp, "choice.wav")])
    ci = idx + 1
    g.append(f"[{ci}:a]aresample=48000,pan=stereo|c0=c0|c1=c0,volume=0.22,asplit={len(wins)}"
             + "".join(f"[ch{j}]" for j in range(len(wins))))
    for j, t in enumerate(wins):
        ms_c = int(t * 1000)
        g.append(f"[ch{j}]adelay={ms_c}|{ms_c}[chd{j}]")
    g.append("[an][sfx]" + "".join(f"[chd{j}]" for j in range(len(wins)))
             + f"amix=inputs={2 + len(wins)}:duration=first:normalize=0,alimiter=limit=0.95[a]")
    enc = (["-c:v", "libx264", "-preset", "medium", "-crf", "30", "-c:a", "aac", "-b:a", "96k"]
           if preview else
           ["-c:v", "libx264", "-preset", "slow", "-crf", "16", "-profile:v", "high",
            "-c:a", "aac", "-b:a", "256k"])
    script = os.path.join(tmp, "graph.txt")
    open(script, "w").write(";\n".join(g))
    total = end_main + d
    subprocess.run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex_script", script,
                    "-map", "[v]", "-map", "[a]", "-r", str(FPS), "-t", f"{total:.3f}", *enc,
                    "-movflags", "+faststart", out], check=True)
    print(f"{out}: {total:.1f}s")


if __name__ == "__main__":
    main()
