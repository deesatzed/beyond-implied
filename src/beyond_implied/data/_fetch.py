"""Shared download helper: save raw bytes (optionally gzipped) plus a hash sidecar."""

from __future__ import annotations

import datetime as dt
import gzip
import hashlib
import json
from pathlib import Path

import requests

USER_AGENT = "beyond-implied/0.0.1 (research; low request rate)"


def fetch_and_store(url: str, dest: Path, *, session: requests.Session | None = None,
                    timeout: float = 30.0, headers: dict | None = None,
                    compress: bool = False) -> tuple[bytes, dict]:
    """GET `url`, write the body to `dest` (gzip if `compress`) and metadata to `dest`.meta.json.

    The SHA-256 is always of the uncompressed body, so it identifies the content received.
    Returns the uncompressed body.
    """
    s = session or requests.Session()
    h = {"User-Agent": USER_AGENT}
    h.update(s.headers if session else {})
    h.update(headers or {})
    r = s.get(url, headers=h, timeout=timeout)
    r.raise_for_status()
    body = r.content
    meta = {
        "url": url,
        "fetched_utc": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "sha256": hashlib.sha256(body).hexdigest(),
        "bytes": len(body),
        "status": r.status_code,
        "compressed": compress,
    }
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(gzip.compress(body) if compress else body)
    Path(str(dest) + ".meta.json").write_text(json.dumps(meta, indent=2))
    return body, meta
