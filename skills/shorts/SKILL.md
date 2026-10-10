---
name: shorts
description: Шортс (Shorts) — turn one raw vertical talking-head take into a punchy YouTube Short / Reels — hook, jump cuts on word boundaries, speaker-driven punch-in crops, "X vs Y" choice cards with winner reveal and chime, karaoke subtitles, mono dialogue fix, blurred subscribe/like ending — with a small review proxy first and a high-quality final (graded and ungraded). Use when the user says "шортс", "сделай шортс", "смонтируй ролик для шортс/рилс", or wants a short vertical edit of a conversation, interview, or "this or that" game.
metadata:
  origin: community
---

# Шортс (Shorts)

A repeatable edit recipe for vertical conversational clips, proven on a Russian
"борщ или оливье?" food-choice game. Everything is driven by one project JSON so the
next video only needs new timings, cards, and subtitles.

## When to Use

- User asks for a Short/Reel/TikTok cut from one longer vertical take ("смонтируй шортс").
- Two people talk; one asks, the other answers ("X или Y", interview, debate, quiz).
- User wants subtitles, picture cards for options, a hook, and a subscribe/like ending.
- User wants a light review copy first and the high-quality master only after approval.

Not for multi-camera documentaries or music-driven montages (see `video-editing`).

## How It Works

### 1. Ingest and assets

```bash
scripts/fetch_assets.sh ./project          # sherpa-onnx + GigaAM ASR, Fluent 3D icons
ffprobe -show_streams src.mp4              # note rotation, fps, audio channels
ffmpeg -i src.mp4 -vf scale=-2:960,fps=25 -crf 26 proxy.mp4   # fast analysis/preview source
```

Cloud sandboxes often block YouTube, stock-photo sites and model hubs. GitHub
(releases, raw) usually works, so models and icons come from there. Wikimedia photos
need both `upload.wikimedia.org` and `thumb.wikimedia.org` allowed. Originals get rate-limited.

### 2. Transcribe with word timestamps

```bash
scripts/transcribe.py proxy.mp4 asr.json
```

Restaurant/room noise hides quiet answers. Re-run on a cleaned copy and on short gap windows:
`pan=mono|c0=c0,highpass=f=120,afftdn=nf=-30,dynaudnorm`. Quiet gaps the first pass skipped
often hold the punchline or the guest's actual choice.

### 3. Decide the edit (write `project.json`)

- **Shots**: cut on word boundaries with ~0.15 s tail. Clipped word endings read as a "рваное начало".
- **Who speaks**: never guess. Crop both faces at 10 fps around the line and look for the moving mouth.
  The guest's answer is easily mistaken for the host's stumble.
- **Stumbles**: drop the false start and keep only the clean repeat of the question.
- **Every choice needs an audible answer** before the winner card lights up. If the answer
  sits in a gap, pull that gap back in.
- **Framing per shot** (`framing` presets): host asks → `L` close-up, guest answers → `R`,
  breathers → `wide`/`med`. Changing every 1.5–3 s gives the "dynamic crops" feel and hides jump cuts.
- **Hook**: first 3–4 s = the strongest emotional moment (reaction + line), then the intro.
- **Ending**: stop on the payoff line, then blur + CTA. Do not run on into post-game chatter.

Project schema (see `examples/food-choice.json`):

| key | meaning |
|-----|---------|
| `shots[]` | `in`/`out` source seconds, `frame` preset, `hook` flag (hook shots play first, main timeline mapping ignores them) |
| `cards[]` | `show`, `win_at` (or null), `hide`, `left`, `right`, `winner`, all in source time |
| `items{}` | per option: `icon` (Fluent name) and optional `photo` file in `photos/` (photo wins if present) |
| `subs[]` | `in`/`out`/`text`. Hand-corrected text, split into 2–3 word karaoke chunks automatically |
| `cta` | blurred tail source range and button labels |
| `audio.mono_channel` | pan expression for a mono mix in both ears. Two lavs on L/R → `0.5*c0+0.5*c1` (measure per speaker first). A single offset stereo mic pair → `c0` or `c1` |

### 4. Review proxy → final

```bash
scripts/build_short.py project.json proxy.mp4 preview.mp4 --preview        # ~3 MB, 540x960
# after approval, from a high-res mezzanine (keeps close-ups sharp):
ffmpeg -i src.mp4 -vf scale=1728:3072:flags=lanczos,fps=30 -crf 14 -g 15 -c:a pcm_s16le mezz.mov
scripts/build_short.py project.json mezz.mov final.mp4
scripts/build_short.py project.json mezz.mov final_grade.mp4 --grade
```

Layout rules baked into the builder (Shorts safe zones): subtitles top (y≈250, 68 px Inter Black,
yellow karaoke fill), cards bottom (y≈1250, 76 %, away from faces), and nothing in the right-hand
action-button column. Audio: per-cut 15–20 ms fades, loudnorm −14 LUFS, chime at each winner
reveal, live sound fades in 0.3 s under the blurred CTA with whoosh + bell + like-click SFX
(all synthesized, so there are no licensing issues).

### 5. Verify before sending

- Contact sheet every 2 s (`fps=1/2,tile=10x3`): faces uncovered, cards and subtitles readable.
- Frames at each winner reveal: the guest is on screen saying the choice.
- Audio envelope over the ending: speech gone after the fade, SFX present.
- Chat attachments cap at 30 MB. Send the preview there and deliver masters another way.

## Examples

Food-choice game, 1:49 raw 4K → 62 s Short:

```text
hook  : facepalm + "…с мамой или с папой?!"          (R close-up)
intro : "Так, ну что, выбирай самое вкусное блюдо"   (wide → L)
rounds: Борщ VS Оливье … Бешбармак VS Окрошка        (L asks / R answers, card + chime)
end   : "Окрошка на квасе победила!" → blur → ПОДПИШИСЬ / СТАВЬ ЛАЙК
```

Typical revision requests and where they land:

| request | change |
|---------|--------|
| "звук в разных наушниках" | `audio.mono_channel`. Check which speaker is louder in each channel; two lavs must be summed, not one picked |
| "рваное начало" | extend shot `out` past the last word end |
| "гость не произносит выбор" | add the answer shot, move `win_at` onto the spoken word |
| "карточки перекрывают" | card overlay y / scale in `build_short.py` |
| "заглушить звук в конце" | CTA `afade` duration |
