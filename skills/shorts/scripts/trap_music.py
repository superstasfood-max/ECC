#!/usr/bin/env python3
"""Dark cinematic trap, 140 BPM (half-time), copyright-free. Filtered intro -> riser -> drop.
usage: trap_music.py OUT.wav TOTAL_BARS DROP_BAR [HYPE_BAR]"""
import sys, wave
import numpy as np

SR, BPM = 48000, 140
B = 60 / BPM; BAR = 4 * B
bars, drop = int(sys.argv[2]), int(sys.argv[3])
hype = int(sys.argv[4]) if len(sys.argv) > 4 else bars
N = int(SR * (bars * BAR + 3.0))
L = np.zeros(N); R = np.zeros(N)
rng = np.random.default_rng(33)


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
    t = tt(0.4)
    return np.tanh(2.5 * np.sin(2 * np.pi * np.cumsum(45 + 120 * np.exp(-t * 28)) / SR) * np.exp(-t * 7))


def clap():
    t = tt(0.35); n = len(t)
    x = np.diff(rng.standard_normal(n + 1))
    env = sum(np.exp(-np.maximum(t - d, 0) * 30) * (t >= d) for d in (0, 0.01, 0.022))
    tail = np.convolve(x * np.exp(-t * 9), np.ones(30) / 30, "same") * 0.6
    return x * env * 0.6 + tail


def hat(len_=0.05):
    t = tt(len_); n = len(t)
    return np.diff(np.diff(rng.standard_normal(n + 2))) * np.exp(-t * 80) * 0.14


def bass808(m, length):
    t = tt(length)
    f = hz(m) * (1 + 0.6 * np.exp(-t * 30))
    return np.tanh(1.8 * np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.minimum(t / 0.005, 1) * np.exp(-t * 0.9)


def pad(notes, length, bright=1.0):
    t = tt(length)
    x = sum(np.sin(2 * np.pi * hz(m) * t * (1 + d)) for m in notes for d in (-0.003, 0.003))
    x += bright * 0.25 * sum(np.sin(2 * np.pi * 2 * hz(m) * t) for m in notes)
    return x / (2 * len(notes)) * np.minimum(t / 0.4, 1) * np.minimum((length - t) / 0.3, 1)


def bell(m):
    t = tt(0.9)
    return (np.sin(2 * np.pi * hz(m) * t) + 0.4 * np.sin(2 * np.pi * hz(m) * 2.76 * t) * np.exp(-t * 6)) * np.exp(-t * 3.5)


def riser(length):
    t = tt(length); n = len(t)
    x = rng.standard_normal(n); y = np.zeros(n); a = 0.0
    for k in range(n):  # rising one-pole low-pass sweep
        c = 0.01 + 0.5 * (k / n) ** 2
        a += c * (x[k] - a); y[k] = a
    return y * (t / length) ** 2 * 3


def boom():
    t = tt(2.5)
    return np.tanh(3 * np.sin(2 * np.pi * np.cumsum(30 + 80 * np.exp(-t * 6)) / SR)) * np.exp(-t * 1.6)


prog = [(45, [57, 60, 64]), (41, [57, 60, 65]), (43, [55, 59, 62]), (40, [55, 59, 64])]  # Am F G Em
melody = [76, 72, 74, 71]
for bar in range(bars):
    t0 = bar * BAR
    root, chord = prog[bar % 4]
    pre = bar < drop
    add(pad(chord, BAR + 0.2, bright=0.4 if pre else 1.0), t0, g=0.35 if pre else 0.28)
    for q in (0, 1.5, 2.5, 3):  # sparse bell motif
        add(bell(melody[bar % 4] + (0 if q < 2 else -5)), t0 + q * B, pan=0.3, g=0.12 if pre else 0.1)
    if pre:
        if bar >= drop - 4:
            for e in range(8):
                add(hat(), t0 + e * B / 2, pan=0.25, g=0.5)
        if bar >= drop - 2:
            add(kick(), t0, g=0.35)
        continue
    # drop / main groove (half-time: kick 1 & "and of 2", clap on 3)
    add(kick(), t0, g=0.9); add(kick(), t0 + 1.5 * B, g=0.7)
    if bar % 2:
        add(kick(), t0 + 3.25 * B, g=0.6)
    add(clap(), t0 + 2 * B, g=0.7)
    add(bass808(root - 12, BAR * 0.95), t0, g=0.75)
    sub = 4 if bar >= hype else 2  # hats: 8ths, 16ths in the hype section, rolls at bar ends
    for e in range(4 * sub):
        add(hat(), t0 + e * B / sub, pan=-0.2, g=0.6 if e % 2 == 0 else 0.4)
    if bar % 4 == 3:
        for e in range(6):
            add(hat(0.03), t0 + 3 * B + e * B / 6, pan=-0.2, g=0.5)

add(riser(2 * BAR), (drop - 2) * BAR, g=0.5)
add(boom(), drop * BAR, g=0.9)
add(boom(), bars * BAR, g=0.8)  # final hit
for k in range(int(SR * 0.15)):  # pre-drop silence gap for impact
    i = int((drop * BAR - 0.15) * SR) + k
    L[i] *= 0.15; R[i] *= 0.15

mix = np.stack([L, R], 1)
mix = np.tanh(mix * 1.1)
mix /= np.abs(mix).max() / 0.9
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype("<i2").tobytes())
