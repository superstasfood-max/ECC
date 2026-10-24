#!/usr/bin/env python3
"""Horizontal unboxing review: tight speech cuts, alternating punch-ins, chapter pills,
neat karaoke subtitles, no music.   usage: edit.py SRC OUT.mp4 [--preview]"""
import json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1920, 1080, 30
FONT_B = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
FONT_DIR = os.path.dirname(FONT_B)
ASR = json.load(open(os.environ.get("REVIEW_ASR", "asr.json")))

# hand-corrected text per ASR segment (keyed by segment start); None = drop the segment
FIX = {
    16.01: "Ну что, небольшая распаковка того, что получилось вчера урвать.",
    21.38: "Самая первая —",
    22.69: "то, что я хотела больше всего, наверное, ну помимо очков Gentle Monster:",
    27.72: "это кастомные Adidas.",
    32.01: "То есть вы покупаете пару —",
    34.15: "в нашем случае две пары — и на одну из них нам",
    39.43: "разрешили сделать кастом бесплатно.",
    42.57: "Вышло вот так.",
    44.71: "То есть вы сами выбираете детальки, шнурки, всякие вот такие штучки. Это, конечно, всё в ограниченном количестве.",
    52.29: "Можно вот такие украшения выбрать.",
    55.91: "Собственно, я не уложилась в тот набор, который входил,",
    59.33: "поэтому",
    60.65: "да, заплатили 199 юаней и набрала ещё всяких. То есть",
    65.70: "тут надо присмотреться.",
    69.13: "Значок Adidas,",
    71.01: "вот эти атласные шнурки,",
    73.16: "вот эта история — какой-то бантик с серебряным сердечком,",
    77.64: "звёздочка — обожаю звёзды.",
    79.69: "Затем вот здесь, на шнурке —",
    83.43: "звёзды.",
    85.09: "Вот такая блестящая история,",
    87.49: "то есть как стразы, да, выглядят.",
    89.51: "Камни.",
    90.76: "На втором",
    92.23: "здесь",
    93.16: "вот такой голубой цветочек,",
    97.00: "цепи.",
    98.53: "Здесь также на втором звезда и вот какая-то такая штучка — конфета,",
    104.68: "сердечко.",
    106.98: "Может быть, что-то ещё. В общем, вот такие кроссовки.",
    110.85: "На самом деле довольно-таки долго мы ждали, но ждали даже не саму работу, а очередь, потому что перед нами",
    120.17: "были только две девушки, но одна из них постоянно-постоянно добавляла что-то. Если честно, там уже как будто даже кроссовок было не видно. То есть она хотела очень много",
    131.17: "аксессуаров.",
    132.52: "Вот мне понравился такой вариант, я сама его придумала,",
    136.49: "как-то представила в голове. Я люблю вот такой голубой, васильковый цвет, леопард обожаю и",
    143.11: "серебро.",
    144.36: "Вот такие кроссы, и мне очень нравятся. Вторые — вторые мы не кастомили. То есть в принципе, может быть, могли за",
    151.75: "твой счёт, но я не уверена.",
    159.14: "Вторые более сдержанные,",
    161.19: "они даже очень классно будут под платье.",
    174.05: "Ой, а что они какие-то такие…",
    177.80: "Блин.",
    179.65: "Что за фигня?",
    181.80: "Мы какие-то здесь сжатые.",
    186.76: "Чуть расстроилась сейчас.",
    190.47: "Вторые — ботиночки, вот такие.",
    193.51: "Они уже на плоском ходу.",
    195.81: "Очень стильно выглядят. Правда, я только что увидела: вот здесь, видите, такая гладкая прям кожа, новая,",
    202.21: "а вот здесь она чуть-чуть — вот, видите — какие-то заломы.",
    209.16: "Так что",
    210.66: "сразу всё проверяйте,",
    214.09: "чтобы не было вот такого.",
    216.26: "И так очень круто. Я ещё покажу, соберу полный образ.",
    219.62: "Надеюсь, что будет очень удобно.",
    222.09: "Мне очень нравится, как выглядит.",
    225.22: "Офигенские.",
    232.90: "Также в Adidas",
    235.33: "я увидела вот такую кепочку.",
    241.19: "Там ещё такого же цвета шопер",
    243.88: "и ещё какая-то фигня… носки? Нет, не носки.",
    247.91: "Шопер, что-то ещё —",
    250.79: "три позиции.",
    252.42: "Мне не очень понравился шопер, он какой-то обычный. Был бы он гигантский — да, прикольно, я бы взяла, а так",
    259.62: "я взяла только",
    262.98: "Офигенно, да?",
    269.22: "Образом вообще прикольно, мне кажется, вот так вот.",
    281.09: "Какую-нибудь кофту, зипку.",
    284.45: "Кстати, вот что ещё купила, но это не вчера было.",
    295.43: "Ещё я купила вот эту",
    298.28: "кофту от Adidas,",
    300.90: "которая везде sold out.",
    304.93: "Смотрите, как прикольно, да?",
    308.01: "Леопардовые кроссы вниз,",
    312.74: "сюда коричневая футболка, может быть, какие-то",
    316.61: "такие аладдины —",
    318.69: "штаны коричневые вот такие,",
    320.97: "либо же вот такие светлые, молочные.",
    325.93: "Мне кажется, будет очень круто.",
    329.54: "И вот такие носочки.",
    331.37: "Ну это так, чисто, наверное,",
    334.89: "под кепку.",
    339.75: "И переходим к самому интересному — это очкам.",
    343.53: "Мы ждали очередь в этот магазин.",
    346.76: None,
    351.08: "Магазин очень классный, там, конечно же, есть вот эти фигуры голов, которые крутятся. Это выглядит максимально реалистично, очень круто, очень современно.",
    362.66: "Действительно, у Gentle Monster очень сильные, крутые",
    368.23: "формы",
    369.83: "и оправы.",
    371.11: "Каждая оправа, которую я мерила, сидела — ну вот правда — потрясающе. Нигде в другом бренде я не встречала, ну чтобы хотя бы там",
    382.47: "больше двух позиций хорошо сидело. Тут же сидела просто охрененно каждая.",
    416.10: "Ребята тоже ушли с покупками.",
    419.56: None,
    424.81: "У Стаса уже была одна оправа от этого бренда, ещё когда мы были в Дубае, ему купили.",
    430.28: "Как-то я тогда не сильно прониклась, а после этого очень сильно начали вируситься видео, классные модели. Я такая: блин, почему я тогда не присмотрелась?",
    440.71: "У них очень классные упаковки, стильные.",
    445.48: "Словарный запас как у гуся, честное слово.",
    449.48: "Мне очень нравится, что у Gentle Monster очень крутые",
    453.16: "упаковки",
    454.92: "и также коробки, в которых",
    457.70: "хранятся сами очки.",
    476.49: "Ой, это те очки, на которые меня, можно сказать, уболтали ребята. Стас…",
    484.49: "Не, вот такие.",
    487.14: "Очень нравится вот этот глянец.",
    490.12: "Я не видела ни у одного бренда именно такого глянца.",
    494.82: "Он какой-то, знаете, такой —",
    497.57: "вау.",
    503.11: None,
    508.97: "Я хочу, чтобы вы обратили отдельное внимание, а именно на душки.",
    519.08: "Офигенские.",
    534.12: "Мне нравится, что есть небольшой эффект затемнения, но",
    537.83: "он есть для людей, которые смотрят на меня. Для меня же это затемнение, знаете, оно настолько мало, то есть оно никак",
    545.45: "не мешает и практически не искажает картинку. То есть она",
    550.98: "практически такая и остаётся. Это круто.",
    556.17: "Вторые.",
    567.37: None,
    571.91: "Кстати, вот знаете, я не знаю, почему в Инстаграме все делают вот так,",
    575.81: "когда распаковывают.",
    579.21: "Напишите мне, пожалуйста, в комментариях, кто знает, зачем так делают.",
    582.79: "Ого!",
    585.06: "Такую упаковочку я первый раз вижу. Она, смотрите, как сумочка.",
    598.82: "Интересно.",
    602.76: "Мы ещё не встречали.",
    613.38: "В таком цвете у меня ещё не было оправы.",
    618.98: "Это было спонтанное решение примерить, в итоге…",
    624.68: "Тадам!",
    626.63: "Пу-дум.",
    632.65: "Круто",
    634.44: "смотрятся,",
    635.69: "удобно сидят.",
    640.33: "Здесь также мне очень нравятся душки.",
    644.29: "В целом вся форма — она, знаете, какая-то… ну просто дорого, круто, стильно выглядит.",
    652.81: None, 658.76: None,
    667.33: "Как мы можем понять, меня на зелёненькое тянет,",
    672.07: "особенно с рыжим цветом волос, мне кажется, вообще круто. В общем, напишите, какие вам очки понравились больше всего",
    678.41: "и по обуви.",
    680.45: None, 681.89: None,
}
START, END = 15.8, 679.6
# silent "show the product" moments to keep longer: (gap start, seconds to keep)
SHOWCASE = {(387.7, 4.0), (460.0, 4.5), (520.3, 5.0), (589.8, 4.0), (604.6, 4.0), (627.1, 5.5)}
CHAPTERS = [(21.38, "01", "Кастомные Adidas"), (159.14, "02", "Вторая пара и ботинки"),
            (232.90, "03", "Кепка и кофта Adidas"), (339.75, "04", "Очки Gentle Monster")]
MAXGAP = 0.35   # longer silences inside/between lines are cut down to this
PUNCH = 1.14    # every other run is a gentle punch-in on the face
FACE = (0.50, 0.40)


def fix_for(seg):
    for k, v in FIX.items():
        if abs(k - seg["s"]) < 0.05:
            return k, v
    return None, None


def build_words():
    """Corrected words with times borrowed proportionally from the ASR words of each segment."""
    out = []
    for seg in ASR:
        k, text = fix_for(seg)
        if text is None or not (START <= seg["s"] <= END):
            continue
        aw, cw = seg["words"], text.split()
        for i, w in enumerate(cw):
            a = aw[min(len(aw) - 1, int(i * len(aw) / len(cw)))]
            b = aw[min(len(aw) - 1, int((i + 1) * len(aw) / len(cw)) - 1 if i + 1 < len(cw) else len(aw) - 1)]
            out.append({"w": w, "s": a["s"], "e": max(b["e"], a["s"] + 0.12), "seg": k})
    return out


def build_cuts(words):
    """Keep speech; squeeze silences to MAXGAP, except listed showcase moments."""
    keep = []
    a = words[0]["s"] - 0.12
    prev = words[0]["e"]
    for w in words[1:]:
        gap = w["s"] - prev
        if gap > MAXGAP:
            show = [d for s, d in SHOWCASE if prev - 2 <= s <= w["s"]]
            keep.append((a, prev + 0.15 + (show[0] if show else 0)))
            a = w["s"] - 0.12 if not show else max(w["s"] - 0.12, keep[-1][1])
        prev = max(prev, w["e"])
    keep.append((a, prev + 0.4))
    merged = []
    for s, e in keep:
        if merged and s - merged[-1][1] < 0.05:
            merged[-1] = (merged[-1][0], max(e, merged[-1][1]))
        elif e - s > 0.25:
            merged.append((s, e))
    return merged


def out_time(cuts, t):
    acc = 0.0
    for a, b in cuts:
        if a <= t <= b:
            return acc + t - a
        if t < a:
            return acc
        acc += b - a
    return acc


def ass_time(t):
    cs = int(round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def write_ass(path, words, cuts):
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Inter ExtraBold,60,&H00FFC87E,&H00FFFFFF,&H00141414,&H8C000000,0,0,0,0,100,100,0,0,1,3.5,2,2,160,160,70,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    # chunk per segment: up to 4 words, break after punctuation
    lines, chunk = [], []
    def flush():
        if chunk:
            lines.append(list(chunk)); chunk.clear()
    for i, w in enumerate(words):
        if chunk and (w["seg"] != chunk[-1]["seg"] or len(chunk) >= 4 or chunk[-1]["w"][-1] in ".?!…:—,"):
            flush()
        chunk.append(w)
    flush()
    ev = []
    for ch in lines:
        t0 = out_time(cuts, ch[0]["s"])
        t1 = out_time(cuts, ch[-1]["e"]) + 0.15
        ks = ""
        for w in ch:
            d = max(1, int(round((out_time(cuts, w["e"]) - out_time(cuts, w["s"])) * 100)))
            ks += f"{{\\k{d}}}{w['w']} "
        ev.append([t0, t1, r"{\fad(60,60)}" + ks.strip()])
    for i in range(len(ev) - 1):  # never overlap
        ev[i][1] = min(ev[i][1], ev[i + 1][0])
    open(path, "w").write(head + "".join(
        f"Dialogue: 0,{ass_time(a)},{ass_time(b)},Sub,,0,0,0,,{t}\n" for a, b, t in ev if b > a + 0.05))


def chapter_png(num, title, path):
    f1 = ImageFont.truetype(FONT_B, 30); f2 = ImageFont.truetype(FONT_B, 40)
    tw = int(ImageDraw.Draw(Image.new("RGBA", (1, 1))).textlength(title, font=f2))
    w, h = 110 + tw + 40, 84
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 42, fill=(15, 15, 18, 200))
    d.rounded_rectangle((10, 10, 94, 74), 32, fill=(126, 200, 255, 255))
    d.text((52, 42), num, font=f1, anchor="mm", fill=(15, 15, 18))
    d.text((112, 42), title, font=f2, anchor="lm", fill="white")
    img.save(path)


def main():
    src, out = sys.argv[1], sys.argv[2]
    preview = "--preview" in sys.argv
    tmp = os.path.join(os.getcwd(), "build"); os.makedirs(tmp, exist_ok=True)
    words = build_words()
    cuts = build_cuts(words)
    total = sum(b - a for a, b in cuts)
    write_ass(os.path.join(tmp, "subs.ass"), words, cuts)
    json.dump(cuts, open(os.path.join(tmp, "cuts.json"), "w"))
    # stage 1: every cut rendered on its own (one decoder at a time), lengths snapped to the frame grid
    seg_dir = os.path.join(tmp, "segs_prev" if preview else "segs_full"); os.makedirs(seg_dir, exist_ok=True)
    lst = open(os.path.join(seg_dir, "list.txt"), "w")
    acc = 0.0
    for k, (a, b) in enumerate(cuts):
        f0, f1 = round(acc * FPS), round((acc + b - a) * FPS); acc += b - a
        nf = f1 - f0
        z = PUNCH if k % 2 else 1.0
        x0 = min(max(FACE[0] - 0.5 / z, 0), 1 - 1 / z); y0 = min(max(FACE[1] - 0.5 / z, 0), 1 - 1 / z)
        ow, oh = (960, 540) if preview else (W, H)
        part = os.path.join(seg_dir, f"{k:03d}.mkv")
        vf = (f"fps={FPS},crop=iw/{z}:ih/{z}:iw*{x0:.4f}:ih*{y0:.4f},scale={ow}:{oh}:flags=lanczos,setsar=1,"
              f"trim=end_frame={nf},setpts=PTS-STARTPTS")
        af = (f"aresample=48000,aformat=channel_layouts=stereo,atrim=end={nf / FPS:.4f},asetpts=PTS-STARTPTS,"
              f"apad=whole_dur={nf / FPS:.4f},afade=t=in:d=0.012,areverse,afade=t=in:d=0.012,areverse")
        venc = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "16" if not preview else "22"]
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{a:.3f}", "-t", f"{b - a + 0.5:.3f}", "-i", src,
                        "-map", "0:v:0", "-map", "0:a:0", "-vf", vf, "-af", af, *venc, "-c:a", "pcm_s16le",
                        part], check=True)
        lst.write(f"file '{part}'\n")
    lst.close()
    inputs = ["-f", "concat", "-safe", "0", "-i", os.path.join(seg_dir, "list.txt")]
    g = [f"[0:v]scale={W}:{H},setsar=1[base]", "[0:a]anull[araw]"]
    n = 1
    last, idx = "base", n
    for c, (t, num, title) in enumerate(CHAPTERS):
        png = os.path.join(tmp, f"ch{c}.png"); chapter_png(num, title, png)
        t0 = out_time(cuts, t); d = 3.2
        inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{d:.2f}", "-i", png]
        g.append(f"[{idx}:v]format=rgba,fade=t=in:d=0.25:alpha=1,fade=t=out:st={d - 0.3:.2f}:d=0.3:alpha=1,"
                 f"setpts=PTS+{t0:.3f}/TB[c{idx}]")
        g.append(f"[{last}][c{idx}]overlay=x='60-40*max(0\\,1-(t-{t0:.3f})/0.3)':y=56:eof_action=pass:"
                 f"enable='between(t,{t0:.3f},{t0 + d:.3f})'[o{idx}]")
        last, idx = f"o{idx}", idx + 1
    sub = os.path.join(tmp, "subs.ass").replace(":", r"\:")
    sc = ",scale=960:540" if preview else ""
    g.append(f"[{last}]subtitles='{sub}':fontsdir={FONT_DIR}{sc},format=yuv420p[v]")
    g.append("[araw]highpass=f=70,afftdn=nf=-28,loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000[a]")
    script = os.path.join(tmp, "graph.txt"); open(script, "w").write(";\n".join(g))
    enc = (["-c:v", "libx264", "-preset", "veryfast", "-crf", "28", "-c:a", "aac", "-b:a", "96k"] if preview else
           ["-c:v", "libx264", "-preset", "slow", "-crf", "17", "-profile:v", "high", "-c:a", "aac", "-b:a", "256k"])
    subprocess.run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex_script", script, "-map", "[v]",
                    "-map", "[a]", "-r", str(FPS), "-t", f"{total:.3f}", *enc, "-movflags", "+faststart", out],
                   check=True)
    print(f"{out}: {total:.1f}s, {n} cuts")


if __name__ == "__main__":
    main()
