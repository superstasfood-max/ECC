#!/usr/bin/env python3
"""Synthesize a bright, upbeat, copyright-free pop groove (112 BPM, C-G-Am-F) to sit under dialogue.
Four-on-the-floor soft kick, claps on 2/4, off-beat hats, bouncy octave bass, plucky chord stabs,
light marimba arpeggio. No lead melody, so it never fights the voice.
usage: upbeat_music.py OUT.wav SECONDS [--seed N]"""
import sys, wave
import numpy as np

SR, BPM = 48000, 112
B = 60 / BPM
dur = float(sys.argv[2])
seed = int(sys.argv[sys.argv.index("--seed") + 1]) if "--seed" in sys.argv else 5
rng = np.random.default_rng(seed)
N = int(SR * dur)
L = np.zeros(N); R = np.zeros(N)


def add(sig, t, pan=0.0, g=1.0):
    i = int(t * SR)
    if i >= N:
        return
    j = min(N, i + len(sig)); s = sig[: j - i] * g
    L[i:j] += s * (1 - max(0, pan)); R[i:j] += s * (1 + min(0, pan))


def hz(m):
    return 440 * 2 ** ((m - 69) / 12)


def tt(sec):
    return np.arange(int(SR * sec)) / SR


def kick():
    t = tt(0.25)
    return np.sin(2 * np.pi * np.cumsum(48 + 90 * np.exp(-t * 40)) / SR) * np.exp(-t * 12)


def clap():
    t = tt(0.18); n = len(t)
    x = np.diff(rng.standard_normal(n + 1))
    env = sum(np.exp(-np.maximum(t - d, 0) * 45) * (t >= d) for d in (0, 0.012, 0.024))
    return x * env * 0.5


def hat(open_=False):
    t = tt(0.16 if open_ else 0.04); n = len(t)
    x = np.diff(np.diff(rng.standard_normal(n + 2)))
    return x * np.exp(-t * (22 if open_ else 90)) * 0.18


def pluck(notes, length=0.22):
    t = tt(length)
    x = sum(2 * ((t * hz(m) * (1 + d)) % 1) - 1 for m in notes for d in (-0.004, 0.004)) / (2 * len(notes))
    bright = np.exp(-t * 18)  # fast-closing "filter": mix of raw saw and its sine core
    core = sum(np.sin(2 * np.pi * hz(m) * t) for m in notes) / len(notes)
    return (x * bright + core * (1 - bright)) * np.exp(-t * 9) * np.minimum(t / 0.004, 1)


def bass(m, length):
    t = tt(length)
    return (np.sin(2 * np.pi * hz(m) * t) + 0.3 * np.sin(4 * np.pi * hz(m) * t)) * \
        np.minimum(t / 0.005, 1) * np.exp(-t * 6)


def marimba(m):
    t = tt(0.4)
    return (np.sin(2 * np.pi * hz(m) * t) + 0.2 * np.sin(2 * np.pi * 4 * hz(m) * t) * np.exp(-t * 30)) * \
        np.exp(-t * 11) * np.minimum(t / 0.002, 1)


prog = [(36, [60, 64, 67]), (43, [59, 62, 67]), (45, [60, 64, 69]), (41, [60, 65, 69])]  # C G Am F
bars = int(np.ceil(dur / (4 * B)))
for bar in range(bars):
    t0 = bar * 4 * B
    root, chord = prog[bar % 4]
    intro = bar < 2
    for beat in range(4):
        tb = t0 + beat * B
        add(kick(), tb, g=0.55 if not intro else 0.35)
        if beat in (1, 3) and not intro:
            add(clap(), tb, pan=0.05, g=0.5)
        add(hat(open_=True), tb + B / 2, pan=0.35, g=0.8)
        for s in (1, 3):
            add(hat(), tb + s * B / 4, pan=-0.3, g=0.6)
        # bouncy octave bass on 8ths
        add(bass(root, B / 2 * 0.9), tb, g=0.5)
        add(bass(root + 12, B / 2 * 0.8), tb + B / 2, g=0.35)
    if not intro:
        for s in (0, 3, 6, 10, 12, 14):  # syncopated stabs (16th grid)
            add(pluck(chord), t0 + s * B / 4, pan=(-0.25 if s % 4 else 0.25), g=0.32)
    arp = chord + [chord[1] + 12]
    for i in range(8):  # light marimba 8th-note arpeggio, every other bar
        if bar % 2:
            add(marimba(arp[i % 4] + 12), t0 + i * B / 2, pan=0.4, g=0.16)

mix = np.stack([L, R], 1)
t = np.arange(N) / SR
mix *= np.minimum(t / 0.8, 1)[:, None]
mix = np.tanh(mix * 1.2) / np.tanh(1.2)
mix /= np.abs(mix).max() / 0.85
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype("<i2").tobytes())
