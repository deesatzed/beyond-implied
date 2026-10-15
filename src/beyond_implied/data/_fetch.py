"""Shared download helper: save raw bytes plus a hash sidecar."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

import requests

USER_AGENT = "beyond-implied/0.0.1 (research; low request rate)"


def fetch_and_store(url: str, dest: Path, *, session: requests.Session | None = None,
                    timeout: float = 30.0) -> tuple[bytes, dict]:
    """GET `url`, write the raw body to `dest` and metadata to `dest` + '.meta.json'."""
    s = session or requests.Session()
    r = s.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
    r.raise_for_status()
    body = r.content
    meta = {
        "url": url,
        "fetched_utc": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "sha256": hashlib.sha256(body).hexdigest(),
        "bytes": len(body),
        "status": r.status_code,
    }
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(body)
    Path(str(dest) + ".meta.json").write_text(json.dumps(meta, indent=2))
    return body, meta
