#!/usr/bin/env python3
"""Soft 'choice confirmed' chime: quick two-note marimba blip. usage: choice_sfx.py OUT.wav"""
import sys, wave
import numpy as np
SR = 48000
n = int(SR * 0.6); t = np.arange(n) / SR
out = np.zeros(n)
for start, f in ((0.0, 880.0), (0.07, 1318.5)):
    i = int(start * SR); tt = t[: n - i]
    tone = (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 4 * f * tt) * np.exp(-tt * 40))
    out[i:] += tone * np.exp(-tt * 9) * np.minimum(tt / 0.002, 1)
out /= np.abs(out).max()
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767 * 0.9).astype("<i2").tobytes())
