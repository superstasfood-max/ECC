#!/usr/bin/env python3
"""Synthesize ending SFX track: whoosh (t=0), bell ding (0.35s), like pop+click (0.95s).
usage: sfx.py OUT.wav DURATION"""
import sys, wave
import numpy as np
SR = 48000
dur = float(sys.argv[2])
out = np.zeros(int(SR * dur))
rng = np.random.default_rng(3)


def put(sig, t, g):
    i = int(t * SR); j = min(len(out), i + len(sig)); out[i:j] += sig[: j - i] * g


# whoosh: noise through a sweeping resonant band, rise-and-fall envelope
n = int(SR * 0.55); t = np.arange(n) / SR
noise = rng.standard_normal(n); y = np.zeros(n); y1 = y2 = 0.0
for k in range(n):
    f = 300 + 3500 * (k / n) ** 1.5; r = 0.985
    w = 2 * np.pi * f / SR
    v = noise[k] + 2 * r * np.cos(w) * y1 - r * r * y2
    y2, y1 = y1, v; y[k] = v
y *= np.sin(np.pi * t / t[-1]) ** 2
put(y / np.abs(y).max(), 0.0, 0.45)
# bell ding: inharmonic partials, long decay
n = int(SR * 1.4); t = np.arange(n) / SR
bell = sum(a * np.sin(2 * np.pi * 1318.5 * m * t) * np.exp(-t * d)
           for m, a, d in ((1, 1, 3.2), (2.76, .45, 5), (5.4, .25, 8), (0.5, .3, 2.5)))
bell *= np.minimum(t / 0.003, 1)
put(bell / np.abs(bell).max(), 0.35, 0.5)
# like: soft pop + click
n = int(SR * 0.12); t = np.arange(n) / SR
pop = np.sin(2 * np.pi * (220 + 600 * np.exp(-t * 40)) * t) * np.exp(-t * 35)
put(pop, 0.95, 0.6)
click = rng.standard_normal(int(SR * 0.008)) * np.exp(-np.arange(int(SR * 0.008)) / 60)
put(click, 0.95, 0.35)
out = np.clip(out, -1, 1)
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767 * 0.9).astype("<i2").tobytes())
