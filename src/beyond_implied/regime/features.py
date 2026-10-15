"""Complexity features: permutation entropy, DFA scaling exponent, recurrence rate."""

from __future__ import annotations

import math

import numpy as np


def _embed(x: np.ndarray, dim: int, delay: int) -> np.ndarray:
    n = x.size - (dim - 1) * delay
    if n <= 0:
        raise ValueError("series too short for this embedding")
    return np.stack([x[i * delay: i * delay + n] for i in range(dim)], axis=1)


def permutation_entropy(x, order: int = 3, delay: int = 1, normalize: bool = True) -> float:
    """Bandt–Pompe permutation entropy. 0 = perfectly ordered, 1 = all patterns equally likely."""
    emb = _embed(np.asarray(x, dtype=float), order, delay)
    patterns = np.argsort(emb, axis=1, kind="stable")
    _, counts = np.unique(patterns, axis=0, return_counts=True)
    p = counts / counts.sum()
    h = float(-(p * np.log(p)).sum())
    return h / math.log(math.factorial(order)) if normalize else h


def dfa_alpha(x, scales=None, order: int = 1) -> float:
    """Detrended fluctuation analysis exponent. ~0.5 white noise, ~1.5 random walk."""
    x = np.asarray(x, dtype=float)
    y = np.cumsum(x - x.mean())
    n = y.size
    if scales is None:
        scales = np.unique(np.logspace(np.log10(8), np.log10(max(16, n // 4)), 12).astype(int))
    fluct, used = [], []
    for s in scales:
        m = n // s
        if m < 2:
            continue
        segs = y[: m * s].reshape(m, s)
        t = np.arange(s)
        rms = []
        for seg in segs:
            coef = np.polyfit(t, seg, order)
            rms.append(np.sqrt(np.mean((seg - np.polyval(coef, t)) ** 2)))
        fluct.append(np.sqrt(np.mean(np.square(rms))))
        used.append(s)
    if len(used) < 3:
        raise ValueError("series too short for DFA")
    slope, _ = np.polyfit(np.log(used), np.log(fluct), 1)
    return float(slope)


def recurrence_rate(x, dim: int = 2, delay: int = 1, eps: float | None = None) -> float:
    """Fraction of distinct embedded-state pairs closer than eps (Chebyshev distance).

    Default eps = 0.2 * std(x). O(n^2): intended for windows of a few hundred points.
    """
    x = np.asarray(x, dtype=float)
    emb = _embed(x, dim, delay)
    if eps is None:
        sd = x.std()
        eps = 0.2 * sd if sd > 0 else 1e-12
    d = np.max(np.abs(emb[:, None, :] - emb[None, :, :]), axis=2)
    n = d.shape[0]
    close = (d < eps).sum() - n  # drop the diagonal
    return float(close / (n * (n - 1)))
