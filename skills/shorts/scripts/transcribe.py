#!/usr/bin/env python3
"""Russian ASR with word timestamps: silero VAD + GigaAM v2 transducer (sherpa-onnx).
Models come from fetch_assets.sh (dir: $SHORTS_MODELS, default ~/.cache/shorts-models).
Tip: for noisy rooms pre-filter: ffmpeg -af "pan=mono|c0=c0,highpass=f=120,afftdn=nf=-30,dynaudnorm"
usage: transcribe.py INPUT_MEDIA OUT.json"""
import json, os, subprocess, sys
import numpy as np
import sherpa_onnx

MODELS = os.environ.get("SHORTS_MODELS", os.path.expanduser("~/.cache/shorts-models"))
M = os.path.join(MODELS, "sherpa-onnx-nemo-transducer-giga-am-v2-russian-2025-04-19")
SR = 16000

raw = subprocess.run(["ffmpeg", "-v", "error", "-i", sys.argv[1], "-vn", "-ac", "1",
                      "-ar", str(SR), "-f", "f32le", "-"], check=True,
                     capture_output=True).stdout
audio = np.frombuffer(raw, dtype=np.float32)

vcfg = sherpa_onnx.VadModelConfig()
vcfg.silero_vad.model = os.path.join(MODELS, "silero_vad.onnx")
vcfg.silero_vad.min_silence_duration = 0.35
vcfg.silero_vad.min_speech_duration = 0.25
vcfg.silero_vad.max_speech_duration = 20
vcfg.sample_rate = SR
vad = sherpa_onnx.VoiceActivityDetector(vcfg, buffer_size_in_seconds=120)

rec = sherpa_onnx.OfflineRecognizer.from_transducer(
    encoder=os.path.join(M, "encoder.int8.onnx"), decoder=os.path.join(M, "decoder.onnx"),
    joiner=os.path.join(M, "joiner.onnx"), tokens=os.path.join(M, "tokens.txt"),
    model_type="nemo_transducer", num_threads=4)

segs = []


def flush():
    while not vad.empty():
        seg = vad.front
        start = seg.start / SR
        st = rec.create_stream()
        st.accept_waveform(SR, np.asarray(seg.samples, dtype=np.float32))
        rec.decode_stream(st)
        r = st.result
        words, cur, t0, t1 = [], "", None, None
        for tok, ts in zip(r.tokens, r.timestamps):
            if tok.startswith("▁") or tok == " ":
                if cur:
                    words.append({"w": cur, "s": round(start + t0, 3), "e": round(start + t1, 3)})
                cur, t0 = tok.lstrip("▁ "), ts
            else:
                if t0 is None:
                    t0 = ts
                cur += tok
            t1 = ts + 0.08
        if cur:
            words.append({"w": cur, "s": round(start + t0, 3), "e": round(start + t1, 3)})
        if words:
            segs.append({"s": round(start, 3), "e": round(start + len(seg.samples) / SR, 3),
                         "text": " ".join(w["w"] for w in words), "words": words})
            print(f"[{start:7.2f}] {segs[-1]['text']}", flush=True)
        vad.pop()


win = vcfg.silero_vad.window_size
for i in range(0, len(audio), win):
    vad.accept_waveform(audio[i:i + win])
    flush()
vad.flush()
flush()
json.dump(segs, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
