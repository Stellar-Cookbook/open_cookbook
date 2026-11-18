#!/usr/bin/env python3
"""Validate cookbook.json entries: schema, SHA-pinned links, live URLs, in-bounds anchors."""

import json
import re
import sys
import urllib.error
import urllib.request
from datetime import date, timedelta
from pathlib import Path

COOKBOOK = Path(__file__).resolve().parent.parent / "cookbook.json"

NETWORKS = {"mainnet", "testnet", "futurenet", "agnostic"}
LINK_RE = re.compile(
    r"^https://github\.com/([^/]+)/([^/]+)/blob/([0-9a-f]{40})/([^#]+?)(?:#L(\d+)(?:-L(\d+))?)?$"
)
TAG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

errors, warnings = [], []
raw_cache = {}


def err(idx, title, msg):
    errors.append(f"  [{idx}] {title!r}: {msg}")


def warn(idx, title, msg):
    warnings.append(f"  [{idx}] {title!r}: {msg}")


def fetch_raw(org, repo, sha, path):
    """Return (http_status | None on network failure, line_count | None)."""
    url = f"https://raw.githubusercontent.com/{org}/{repo}/{sha}/{path}"
    if url in raw_cache:
        return raw_cache[url]
    req = urllib.request.Request(url, headers={"User-Agent": "open-cookbook-validate"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            body = r.read().decode("utf-8", "replace")
            raw_cache[url] = (r.status, body.count("\n") + (0 if body.endswith("\n") else 1))
    except urllib.error.HTTPError as e:
        raw_cache[url] = (e.code, None)
    except (urllib.error.URLError, TimeoutError):
        raw_cache[url] = (None, None)
    return raw_cache[url]


def check_entry(idx, inst):
    title = inst.get("title", "<untitled>")

    if not isinstance(inst, dict):
        err(idx, title, "entry must be an object")
        return

    for field in ("title", "link", "why", "network", "submitted_on", "verified_by_org"):
        if field not in inst:
            err(idx, title, f"missing required field {field!r}")
        elif not isinstance(inst[field], str):
            err(idx, title, f"{field!r} must be a string")

    if isinstance(inst.get("title"), str) and not inst["title"].strip():
        err(idx, title, "title must not be blank")
    if isinstance(inst.get("why"), str) and not inst["why"].strip():
        err(idx, title, "why must not be blank")

    net = inst.get("network")
    if isinstance(net, str) and net not in NETWORKS:
        err(idx, title, f"network {net!r} must be one of {sorted(NETWORKS)}")

    sub = inst.get("submitted_on")
    if isinstance(sub, str):
        try:
            d = date.fromisoformat(sub)
            if d > date.today() + timedelta(days=1):
                warn(idx, title, f"submitted_on {sub} is in the future")
        except ValueError:
            err(idx, title, f"submitted_on {sub!r} is not a valid YYYY-MM-DD date")

    if "tags" in inst:
        tags = inst["tags"]
        if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
            err(idx, title, "tags must be an array of strings")
        elif not 1 <= len(tags) <= 3:
            err(idx, title, "tags should contain 1-3 labels")
        else:
            bad = [t for t in tags if not TAG_RE.fullmatch(t)]
            if bad:
                err(idx, title, f"tags must be lowercase kebab-case: {bad}")

    link = inst.get("link", "")
    if not isinstance(link, str):
        return
    m = LINK_RE.match(link)
    if not m:
        err(idx, title, "link must be github.com/<org>/<repo>/blob/<40-char-commit-sha>/<path> "
                         "(optionally #Lx or #Lx-Ly) — not a branch or tag")
        return
    org, repo, sha, path, l1, l2 = m.groups()

    status, nlines = fetch_raw(org, repo, sha, path)
    if status is None:
        warn(idx, title, f"could not fetch raw file (network issue?): {org}/{repo}@{sha[:7]}/{path}")
    elif status != 200:
        err(idx, title, f"raw file returned HTTP {status}: {org}/{repo}@{sha[:7]}/{path}")
    elif l1:
        end = int(l2) if l2 else int(l1)
        if l2 and int(l2) < int(l1):
            err(idx, title, f"anchor range #L{l1}-L{l2} is reversed")
        elif end > nlines:
            err(idx, title, f"anchor L{end} beyond end of file ({nlines} lines)")


def main():
    try:
        data = json.loads(COOKBOOK.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"FAIL: cannot parse {COOKBOOK.name}: {e}")
        return 1

    instances = data.get("instances") if isinstance(data, dict) else None
    if not isinstance(instances, list):
        print("FAIL: cookbook.json must contain an 'instances' array")
        return 1

    seen = {}
    for i, inst in enumerate(instances):
        t = inst.get("title") if isinstance(inst, dict) else None
        if t in seen:
            warn(i, t, f"duplicate title (also at index {seen[t]})")
        seen[t] = i
        check_entry(i, inst)

    print(f"checked {len(instances)} entries against {len(raw_cache)} unique files")
    for w in warnings:
        print(f"WARN {w}")
    for e in errors:
        print(f"FAIL {e}")
    print("OK" if not errors else f"{len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
