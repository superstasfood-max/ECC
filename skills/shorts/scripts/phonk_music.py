#!/usr/bin/env python3
"""Drift-phonk style hype track (150 BPM), copyright-free: filtered cowbell intro + riser,
then full drop with punchy kicks, distorted 808, 16th hats and a cowbell riff.
usage: phonk_music.py OUT.wav TOTAL_BARS DROP_BAR [HYPE_BAR] [BPM]"""
import sys, wave
import numpy as np

SR = 48000
bars, drop = int(sys.argv[2]), int(sys.argv[3])
hype = int(sys.argv[4]) if len(sys.argv) > 4 else bars
BPM = float(sys.argv[5]) if len(sys.argv) > 5 else 150
B = 60 / BPM; BAR = 4 * B
N = int(SR * (bars * BAR + 3.0))
L = np.zeros(N); R = np.zeros(N)
rng = np.random.default_rng(150)


def add(sig, t, pan=0.0, g=1.0):
    i = int(t * SR)
    if i >= N or i < 0:
        return
    j = min(N, i + len(sig)); s = sig[: j - i] * g
    L[i:j] += s * (1 - max(0, pan)); R[i:j] += s * (1 + min(0, pan))


def tt(sec):
    return np.arange(int(SR * sec)) / SR


def hz(m):
    return 440 * 2 ** ((m - 69) / 12)


def kick():
    t = tt(0.3)
    return np.tanh(3 * np.sin(2 * np.pi * np.cumsum(50 + 140 * np.exp(-t * 35)) / SR) * np.exp(-t * 11))


def snare():
    t = tt(0.25); n = len(t)
    x = np.diff(rng.standard_normal(n + 1))
    return np.tanh(2 * (0.8 * x * np.exp(-t * 16) + 0.5 * np.sin(2 * np.pi * 200 * t) * np.exp(-t * 30)))


def hat(len_=0.04, open_=False):
    t = tt(0.18 if open_ else len_); n = len(t)
    return np.diff(np.diff(rng.standard_normal(n + 2))) * np.exp(-t * (20 if open_ else 90)) * 0.15


def b808(m, length):
    t = tt(length)
    f = hz(m) * (1 + 0.9 * np.exp(-t * 40))
    return np.tanh(3.2 * np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.minimum(t / 0.004, 1) * np.exp(-t * 1.6)


def cowbell(m, length=0.22):
    t = tt(length)
    f1, f2 = hz(m), hz(m) * 1.48  # two detuned square-ish partials = classic 808 cowbell
    x = np.sign(np.sin(2 * np.pi * f1 * t)) + np.sign(np.sin(2 * np.pi * f2 * t))
    x = np.convolve(x, np.ones(6) / 6, "same")
    return x * np.exp(-t * 10) * np.minimum(t / 0.002, 1) * 0.35


def riser(length):
    t = tt(length); n = len(t)
    x = rng.standard_normal(n); y = np.zeros(n); a = 0.0
    for k in range(n):
        c = 0.01 + 0.5 * (k / n) ** 2
        a += c * (x[k] - a); y[k] = a
    return y * (t / length) ** 2 * 3


def impact():
    t = tt(2.0)
    return np.tanh(3 * np.sin(2 * np.pi * np.cumsum(35 + 90 * np.exp(-t * 7)) / SR)) * np.exp(-t * 2)


# 2-bar cowbell riff in C# minor (16th grid positions, midi notes)
RIFF = [(0, 73), (3, 73), (6, 76), (8, 75), (10, 73), (12, 71), (14, 73),
        (16, 73), (19, 73), (22, 76), (24, 78), (26, 76), (28, 75), (30, 71)]
ROOTS = [37, 37, 40, 35]  # C#, C#, E, B
for bar in range(bars):
    t0 = bar * BAR
    s16 = B / 4
    pre = bar < drop
    for pos, m in RIFF:
        if (pos // 16) == bar % 2:
            add(cowbell(m), t0 + (pos % 16) * s16, pan=0.15, g=0.5 if pre else 0.65)
    if pre:
        if bar >= drop - 2:
            for e in range(8):
                add(hat(), t0 + e * B / 2, g=0.6)
        continue
    root = ROOTS[bar % 4]
    for beat in range(4):  # punchy full-time groove
        add(kick(), t0 + beat * B, g=0.85 if beat % 2 == 0 else 0.6)
    add(kick(), t0 + 2.75 * B, g=0.55)
    add(snare(), t0 + B, g=0.6); add(snare(), t0 + 3 * B, g=0.6)
    add(b808(root - 12, 1.4 * B), t0, g=0.7)
    add(b808(root - 12, 0.9 * B), t0 + 2.5 * B, g=0.6)
    sub = 4 if bar >= hype else 2
    for e in range(4 * sub):
        add(hat(), t0 + e * B / sub, pan=-0.25, g=0.55 if e % 2 == 0 else 0.35)
    add(hat(open_=True), t0 + 3.5 * B, pan=0.3, g=0.6)
    if bar % 4 == 3:
        for e in range(8):  # snare roll into the next phrase
            add(snare(), t0 + 3 * B + e * B / 8, g=0.15 + 0.05 * e)

add(riser(2 * BAR), (drop - 2) * BAR, g=0.55)
add(impact(), drop * BAR, g=0.9)
add(impact(), bars * BAR, g=0.85)
i0, i1 = int((drop * BAR - 0.18) * SR), int(drop * BAR * SR)  # tiny silence before the drop
L[i0:i1] *= 0.1; R[i0:i1] *= 0.1

mix = np.stack([L, R], 1)
pre_end = int(drop * BAR * SR)  # muffle the intro so the drop opens up
for ch in range(2):
    y = mix[:pre_end, ch].copy(); a = 0.0
    out = np.empty_like(y)
    for k, v in enumerate(y):
        a += 0.12 * (v - a); out[k] = a
    mix[:pre_end, ch] = out * 1.6
mix = np.tanh(mix * 1.2)
mix /= np.abs(mix).max() / 0.9
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype("<i2").tobytes())
