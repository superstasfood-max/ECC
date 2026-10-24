#!/usr/bin/env python3
"""UFC 333 trip recap Short: beat-synced cuts, settle punch per cut, flash at the drop,
section chips, final title, trap bed + quiet live sound.   usage: ufc_edit.py SRC_DIR EXT OUT [--preview]"""
import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, (30 if "--preview" in sys.argv else 60)
BPM = 150
BAR = 4 * 60 / BPM
FONT = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
RED = (210, 10, 10, 255)

# (clip, in-point seconds, length in BEATS) — part 1 = 8 beats, then 2-beat cuts
SHOTS = [
    ("IMG_6518", 1.6, 8),
    ("IMG_6513", 0.6, 2), ("IMG_6514", 1.0, 2), ("IMG_6517", 2.4, 2), ("IMG_6523", 1.0, 2),
    ("IMG_6515", 6.6, 2), ("IMG_6522", 0.3, 2), ("IMG_3554", 1.2, 2), ("IMG_3615", 1.0, 2),
    ("IMG_6511", 1.0, 2), ("IMG_6547", 19.6, 2), ("IMG_6548", 14.2, 2), ("IMG_6548", 18.0, 4),
]
DROP_BAR = 2
HYPE_BAR = 4
CHIPS = []
CAPTIONS = [(0, 8, "смотреть UFC\nпо телевизору"), (8, None, "смотреть UFC\nвживую")]
SETTLE = 1.07  # each cut lands slightly tight and eases out over ~0.3 s


def chip(text, path, size=58):
    f = ImageFont.truetype(FONT, size)
    tw = int(ImageDraw.Draw(Image.new("RGBA", (1, 1))).textlength(text, font=f))
    w, h, sk = tw + 90, 100, 26
    img = Image.new("RGBA", (w + sk, h), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    d.polygon([(sk, 0), (w + sk, 0), (w, h), (0, h)], fill=RED)
    d.text(((w + sk) / 2, h / 2 + 2), text, font=f, anchor="mm", fill="white")
    img.save(path)


def title(path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    big = ImageFont.truetype(FONT, 230); mid = ImageFont.truetype(FONT, 64)
    d.text((W / 2 + 6, 860 + 8), "UFC 333", font=big, anchor="mm", fill=(0, 0, 0, 160))
    d.text((W / 2, 860), "UFC 333", font=big, anchor="mm", fill="white")
    d.polygon([(250, 1010), (850, 1010), (830, 1090), (230, 1090)], fill=RED)
    d.text((W / 2 - 10, 1052), "АБУ-ДАБИ · 24.10", font=mid, anchor="mm", fill="white")
    img.save(path)


def caption(text, path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    f = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Bold.otf", 76)
    d.multiline_text((W / 2, 1380), text, font=f, anchor="mm", align="center", fill="white",
                     stroke_width=7, stroke_fill="black", spacing=14)
    img.save(path)


def main():
    src_dir, ext, out = sys.argv[1], sys.argv[2], sys.argv[3]
    preview = "--preview" in sys.argv
    tmp = os.path.join(os.getcwd(), "build"); os.makedirs(tmp, exist_ok=True)
    beats = sum(s[2] for s in SHOTS)
    bars = beats // 4
    total = beats * BAR / 4
    music = os.path.join(tmp, "music.wav")
    subprocess.run([sys.executable, os.path.join(HERE, "..", "scripts", "phonk_music.py"), music, str(bars + 1), str(DROP_BAR), str(HYPE_BAR), str(BPM)],
                   check=True)
    inputs, g, cat, t = [], [], "", 0.0
    for k, (clip, a, nb) in enumerate(SHOTS):
        f0, f1 = round(t * FPS), round((t + nb * BAR / 4) * FPS); t += nb * BAR / 4
        nf, d = f1 - f0, (f1 - f0) / FPS
        inputs += ["-ss", f"{a:.2f}", "-t", f"{d + 0.5:.2f}", "-i", os.path.join(src_dir, clip + ext)]
        u = f"clip(in/{FPS}/0.3,0,1)"
        z = f"{SETTLE}-{SETTLE - 1}*{u}*{u}*(3-2*{u})"
        g.append(f"[{k}:v]fps={FPS},scale={W * 2}:{H * 2}:flags=bicubic,setpts=PTS-STARTPTS,"
                 f"zoompan=z='{z}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s={W}x{H}:fps={FPS},"
                 f"setsar=1,trim=end_frame={nf},setpts=PTS-STARTPTS[v{k}]")
        g.append(f"[{k}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=end={d:.4f},apad=whole_dur={d:.4f},"
                 f"asetpts=PTS-STARTPTS,afade=t=in:d=0.02,areverse,afade=t=in:d=0.02,areverse[a{k}]")
        cat += f"[v{k}][a{k}]"
    n = len(SHOTS)
    g.append(f"{cat}concat=n={n}:v=1:a=1[cv][live]")
    drop_t = DROP_BAR * BAR
    # white flash on the drop + light contrast/vibrance for the arena look
    g.append(f"[cv]eq=contrast=1.05:saturation=1.08,"
             f"drawbox=x=0:y=0:w=iw:h=ih:color=white@1:t=fill:enable='between(t,{drop_t - 0.03:.3f},{drop_t + 0.12:.3f})'[base]")
    last, idx = "base", n
    for c, (bar, text) in enumerate(CHIPS):
        png = os.path.join(tmp, f"chip{c}.png"); chip(text, png)
        t0 = bar * BAR + 0.1; dur = 2 * BAR - 0.2
        inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.2f}", "-i", png]
        g.append(f"[{idx}:v]format=rgba,fade=t=in:d=0.12:alpha=1,fade=t=out:st={dur - 0.2:.2f}:d=0.2:alpha=1,"
                 f"setpts=PTS+{t0:.3f}/TB[c{idx}]")
        g.append(f"[{last}][c{idx}]overlay=x='70-120*max(0\\,1-(t-{t0:.3f})/0.18)':y=210:eof_action=pass:"
                 f"enable='between(t,{t0:.3f},{t0 + dur:.3f})'[o{idx}]")
        last, idx = f"o{idx}", idx + 1
    for c, (b0, b1, text) in enumerate(CAPTIONS):
        png = os.path.join(tmp, f"cap{c}.png"); caption(text.replace("\\n", "\n"), png)
        # clear gap around the flash: old line leaves before it, new line fades in after it
        t0 = b0 * BAR / 4 + (0.12 if b0 else 0); t1 = (b1 * BAR / 4 - 0.12) if b1 else total + 1.5
        inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{t1 - t0:.2f}", "-i", png]
        fi = "fade=t=in:d=0.12:alpha=1," if b0 else ""
        fo = f"fade=t=out:st={t1 - t0 - 0.08:.2f}:d=0.08:alpha=1," if b1 else ""
        g.append(f"[{idx}:v]format=rgba,{fi}{fo}setpts=PTS+{t0:.3f}/TB[c{idx}]")
        g.append(f"[{last}][c{idx}]overlay=0:0:eof_action=pass:enable='between(t,{t0:.3f},{t1 - 0.001:.3f})'[o{idx}]")
        last, idx = f"o{idx}", idx + 1
    sc = ",scale=540:960" if preview else ""
    g.append(f"[{last}]tpad=stop_mode=clone:stop_duration=1.5{sc},fade=t=out:st={total + 0.6:.2f}:d=0.9,format=yuv420p[v]")
    inputs += ["-i", music]
    g.append("[live]highpass=f=90,volume=0.22,apad[lv]")
    g.append(f"[{idx}:a]aresample=48000,volume=0.9[mu]")
    g.append(f"[mu][lv]amix=inputs=2:duration=first:normalize=0,afade=t=out:st={total + 0.3:.2f}:d=1.2,"
             "loudnorm=I=-14:TP=-1:LRA=11[a]")
    script = os.path.join(tmp, "graph.txt"); open(script, "w").write(";\n".join(g))
    enc = (["-c:v", "libx264", "-preset", "veryfast", "-crf", "27", "-c:a", "aac", "-b:a", "128k"] if preview else
           ["-c:v", "libx264", "-preset", "slow", "-crf", "14", "-profile:v", "high", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "320k"])
    subprocess.run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex_script", script, "-map", "[v]",
                    "-map", "[a]", "-r", str(FPS), "-t", f"{total + 1.5:.2f}", *enc, "-movflags", "+faststart", out],
                   check=True)
    print(f"{out}: {total + 1.5:.1f}s, {n} shots, {bars} bars")


if __name__ == "__main__":
    main()
