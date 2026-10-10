#!/usr/bin/env python3
"""Synthesize a calm, copyright-free lo-fi bed (84 BPM, Am7-Fmaj7-Cmaj7-G6) to sit under dialogue.
Soft electric-piano chords, muted kick/rim, shaker, round bass, faint vinyl noise, all low-passed.
usage: lofi_music.py OUT.wav SECONDS [--seed N]"""
import sys, wave
import numpy as np

SR, BPM = 48000, 84
B = 60 / BPM
dur = float(sys.argv[2])
seed = int(sys.argv[sys.argv.index("--seed") + 1]) if "--seed" in sys.argv else 11
rng = np.random.default_rng(seed)
N = int(SR * dur)
L = np.zeros(N); R = np.zeros(N)


def add(sig, t, pan=0.0, g=1.0):
    i = int(t * SR)
    if i >= N:
        return
    j = min(N, i + len(sig)); s = sig[: j - i] * g
    L[i:j] += s * (1 - max(0, pan)); R[i:j] += s * (1 + min(0, pan))


def onepole(x, a):
    y = np.empty_like(x); acc = 0.0
    for i, v in enumerate(x):
        acc += a * (v - acc); y[i] = acc
    return y


def hz(m):
    return 440 * 2 ** ((m - 69) / 12)


def epiano(notes, length):
    n = int(SR * length); t = np.arange(n) / SR
    env = np.minimum(t / 0.01, 1) * np.exp(-t * 1.1)
    trem = 1 + 0.08 * np.sin(2 * np.pi * 4.5 * t)
    x = sum(np.sin(2 * np.pi * hz(m) * t) + 0.25 * np.sin(4 * np.pi * hz(m) * t) * np.exp(-t * 4)
            for m in notes) / len(notes)
    return x * env * trem


def kick():
    n = int(SR * 0.3); t = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(50 + 60 * np.exp(-t * 30)) / SR) * np.exp(-t * 9)


def rim():
    n = int(SR * 0.08); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 1700 * t) * 0.4 + rng.standard_normal(n) * 0.3) * np.exp(-t * 60)


def shaker():
    n = int(SR * 0.06); t = np.arange(n) / SR
    x = np.diff(rng.standard_normal(n + 1))
    return x * np.exp(-t * 55) * np.minimum(t / 0.01, 1) * 0.12


def bass(m, length):
    n = int(SR * length); t = np.arange(n) / SR
    return np.sin(2 * np.pi * hz(m) * t) * np.minimum(t / 0.02, 1) * np.exp(-t * 1.8)


prog = [(45, [57, 60, 64, 67]), (41, [53, 57, 60, 64]), (48, [55, 59, 60, 64]), (43, [55, 59, 62, 64])]
bars = int(np.ceil(dur / (4 * B)))
for bar in range(bars):
    t0 = bar * 4 * B
    root, chord = prog[bar % 4]
    add(epiano([m + 12 for m in chord[1:]], 4 * B + 0.5), t0, pan=-0.2, g=0.3)
    add(epiano(chord, 4 * B + 0.5), t0, g=0.55)
    add(epiano(chord[1:], 1.2), t0 + 2.5 * B, pan=0.25, g=0.25)  # lazy off-beat re-voice
    add(bass(root, 2 * B), t0, g=0.5); add(bass(root + 7, 1.5 * B), t0 + 2.5 * B, g=0.35)
    if bar >= 1:  # drums enter after one bar
        for beat in range(4):
            sw = 0.03 if beat % 2 else 0.0  # a little swing
            if beat in (0, 2):
                add(kick(), t0 + beat * B, g=0.45)
            else:
                add(rim(), t0 + beat * B + sw, pan=-0.15, g=0.22)
            for e in range(2):
                add(shaker(), t0 + beat * B + e * B / 2 + (0.04 if e else 0), pan=0.3, g=0.9)

mix = np.stack([L, R], 1)
mix[:, 0] = onepole(mix[:, 0], 0.4); mix[:, 1] = onepole(mix[:, 1], 0.4)  # gentle low-pass, keeps phone-speaker presence
mix += rng.standard_normal(mix.shape) * 0.004  # faint vinyl hiss
t = np.arange(N) / SR
mix *= np.minimum(t / 1.5, 1)[:, None]  # fade in
mix /= np.abs(mix).max() / 0.8
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype("<i2").tobytes())
