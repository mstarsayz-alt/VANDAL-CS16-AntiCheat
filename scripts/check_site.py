#!/usr/bin/env python3
"""Static checks for the VANDAL site: links, sitemap, JSON-LD, SHA-256 and build consistency."""
import json
import pathlib
import re
import sys
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = "https://mstarsayz-alt.github.io/VANDAL-CS16-AntiCheat/"
PREFIX = "/VANDAL-CS16-AntiCheat/"
errors = []


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs, self.ids, self.jsonld, self.meta = [], set(), [], {}
        self.canonical = None
        self._in_ld = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        for key in ("href", "src"):
            if a.get(key):
                self.refs.append(a[key])
        if tag == "link" and a.get("rel") == "canonical":
            self.canonical = a.get("href")
        if tag == "meta":
            k = a.get("property") or a.get("name")
            if k:
                self.meta[k] = a.get("content", "")
        if tag == "script" and a.get("type") == "application/ld+json":
            self._in_ld = True
            self.jsonld.append("")

    def handle_endtag(self, tag):
        if tag == "script":
            self._in_ld = False

    def handle_data(self, data):
        if self._in_ld:
            self.jsonld[-1] += data


pages = {}
for f in sorted(ROOT.glob("*.html")):
    p = Page()
    p.feed(f.read_text(encoding="utf-8"))
    pages[f.name] = p

for name, p in pages.items():
    for ref in p.refs:
        if ref.startswith(("http://", "https://", "mailto:")):
            continue
        path, _, frag = ref.partition("#")
        if path.startswith(PREFIX):
            path = path[len(PREFIX):]
        elif path.startswith("/"):
            errors.append(f"{name}: root-absolute link outside site prefix: {ref}")
            continue
        target = path or name
        if not (ROOT / target).is_file():
            errors.append(f"{name}: broken link {ref}")
        elif frag and target.endswith(".html") and frag not in pages[target].ids:
            errors.append(f"{name}: missing anchor #{frag} in {target}")
    for i, block in enumerate(p.jsonld):
        try:
            json.loads(block)
        except ValueError as e:
            errors.append(f"{name}: invalid JSON-LD block {i}: {e}")
    if name == "404.html":
        continue
    expected = BASE if name == "index.html" else BASE + name
    if p.canonical != expected:
        errors.append(f"{name}: canonical {p.canonical!r} != {expected!r}")
    if p.meta.get("og:url") != expected:
        errors.append(f"{name}: og:url does not match canonical")
    for key in ("description", "og:title", "og:image"):
        if not p.meta.get(key):
            errors.append(f"{name}: missing meta {key}")
    if p.meta.get("og:image", "").endswith(".svg"):
        errors.append(f"{name}: og:image must be raster (PNG/JPG), not SVG")

sitemap = set(re.findall(r"<loc>([^<]+)</loc>", (ROOT / "sitemap.xml").read_text()))
indexable = {BASE if n == "index.html" else BASE + n for n in pages if n != "404.html"}
for missing in sorted(indexable - sitemap):
    errors.append(f"sitemap.xml: missing {missing}")
for extra in sorted(sitemap - indexable):
    errors.append(f"sitemap.xml: lists unknown page {extra}")

sums = {}
for line in (ROOT / "downloads/SHA256SUMS.txt").read_text().splitlines():
    if line.strip():
        digest, fname = line.split(maxsplit=1)
        sums[fname.lstrip("*")] = digest.lower()
exe_hash = sums.get("VANDAL.exe")
if not exe_hash or not re.fullmatch(r"[0-9a-f]{64}", exe_hash):
    errors.append("SHA256SUMS.txt: missing or malformed VANDAL.exe digest")
else:
    found = set(re.findall(r"\b[0-9a-fA-F]{64}\b", (ROOT / "download.html").read_text(encoding="utf-8")))
    if {h.lower() for h in found} != {exe_hash}:
        errors.append(f"download.html: SHA-256 values {sorted(found)} do not match SHA256SUMS.txt ({exe_hash})")

builds = {}
for name in pages:
    for b in re.findall(r"\b\d{4}\.\d{2}\.\d{2}\.\d+-[\w-]+", (ROOT / name).read_text(encoding="utf-8")):
        builds.setdefault(b, []).append(name)
if len(builds) > 1:
    errors.append(f"inconsistent build strings across pages: {builds}")

json.loads((ROOT / "site.webmanifest").read_text())

if errors:
    print("\n".join(f"ERROR: {e}" for e in errors))
    sys.exit(1)
print(f"OK: {len(pages)} pages checked")
