#!/usr/bin/env python3
"""Post-build verification gate for flyovercon.ink.

Run after build.py. Exits non-zero if any check fails.
No zip is packaged unless this passes clean.
"""
import glob, json, os, re, sys

OUT = "site"
BASE = "https://www.flyovercon.ink"

# Standalone pages that ship noindex on purpose. They are exempt from the
# JSON-LD and sitemap-membership rules, and are checked instead for the
# opposite: they must carry a noindex robots tag and must stay out of
# sitemap.xml. See RAW_PAGES in build.py.
NOINDEX_PAGES = {"survey.html"}
failures = []
notes = []


def fail(msg):
    failures.append(msg)


def page_files():
    return sorted(glob.glob(os.path.join(OUT, "*.html")))


def read(p):
    return open(p, encoding="utf-8").read()


# ---------------------------------------------------------------- checks
def check_placeholder_links(pages):
    for p, html in pages:
        for m in re.findall(r'href="#"', html):
            fail(f"{p}: placeholder href=\"#\"")


def check_noopener(pages):
    for p, html in pages:
        for tag in re.findall(r"<a\b[^>]*>", html):
            href = re.search(r'href="([^"]*)"', tag)
            if not href:
                continue
            url = href.group(1)
            if not url.startswith("http"):
                continue
            if url.startswith(BASE):
                continue
            if 'rel="noopener"' not in tag:
                fail(f"{p}: external link missing rel=noopener -> {url}")


def check_internal_links_extensionless(pages):
    """Clean-URL regression guard: no internal links may end in .html"""
    for p, html in pages:
        for url in re.findall(r'href="([^"]*)"', html):
            if url.startswith("http") and not url.startswith(BASE):
                continue  # external, not ours
            if url.endswith(".html"):
                fail(f"{p}: internal link still uses .html -> {url}")


def check_titles_descriptions(pages):
    titles, descs = {}, {}
    for p, html in pages:
        t = re.search(r"<title>(.*?)</title>", html, re.S)
        d = re.search(r'<meta name="description" content="(.*?)"', html, re.S)
        if not t:
            fail(f"{p}: missing <title>")
        else:
            titles.setdefault(t.group(1).strip(), []).append(p)
        if not d:
            fail(f"{p}: missing meta description")
        else:
            descs.setdefault(d.group(1).strip(), []).append(p)
    for val, ps in titles.items():
        if len(ps) > 1:
            fail(f"duplicate <title> across {ps}")
    for val, ps in descs.items():
        if len(ps) > 1:
            fail(f"duplicate meta description across {ps}")


def check_single_h1(pages):
    for p, html in pages:
        n = len(re.findall(r"<h1\b", html))
        if n != 1:
            fail(f"{p}: expected 1 <h1>, found {n}")


def check_jsonld(pages):
    for p, html in pages:
        if p in NOINDEX_PAGES:
            continue
        blocks = re.findall(
            r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
        if not blocks:
            fail(f"{p}: no JSON-LD block")
        for b in blocks:
            try:
                json.loads(b)
            except json.JSONDecodeError as e:
                fail(f"{p}: invalid JSON-LD ({e})")


def check_em_dashes(pages):
    for p, html in pages:
        if "\u2014" in html or "&mdash;" in html:
            fail(f"{p}: contains em dash")
    for extra in ("llms.txt", "robots.txt", "sitemap.xml"):
        fp = os.path.join(OUT, extra)
        if os.path.exists(fp):
            t = read(fp)
            if "\u2014" in t or "&mdash;" in t:
                fail(f"{extra}: contains em dash")


def check_canonicals(pages):
    seen = {}
    for p, html in pages:
        m = re.search(r'<link rel="canonical" href="([^"]*)"', html)
        if not m:
            fail(f"{p}: missing canonical")
            continue
        url = m.group(1)
        if not url.startswith(BASE):
            fail(f"{p}: canonical not on www apex -> {url}")
        if url.endswith(".html"):
            fail(f"{p}: canonical still uses .html -> {url}")
        seen.setdefault(url, []).append(p)
    for url, ps in seen.items():
        if len(ps) > 1:
            fail(f"duplicate canonical {url} across {ps}")


def check_sitemap(pages):
    fp = os.path.join(OUT, "sitemap.xml")
    if not os.path.exists(fp):
        fail("sitemap.xml missing")
        return
    sm = read(fp)
    locs = set(re.findall(r"<loc>([^<]*)</loc>", sm))
    canons = set()
    for p, html in pages:
        m = re.search(r'<link rel="canonical" href="([^"]*)"', html)
        if not m:
            continue
        if p in NOINDEX_PAGES:
            if m.group(1) in locs:
                fail(f"{p}: noindex page must stay out of sitemap -> {m.group(1)}")
            continue
        canons.add(m.group(1))
    for c in canons - locs:
        fail(f"canonical not in sitemap: {c}")
    for l in locs - canons:
        fail(f"sitemap URL has no page: {l}")
    for l in locs:
        if l.endswith(".html"):
            fail(f"sitemap entry still uses .html -> {l}")


def check_vercel_config():
    fp = os.path.join(OUT, "vercel.json")
    if not os.path.exists(fp):
        fail("vercel.json missing from site/")
        return
    cfg = json.loads(read(fp))
    if cfg.get("cleanUrls") is not True:
        fail("vercel.json: cleanUrls not enabled")
    if cfg.get("trailingSlash") is not False:
        fail("vercel.json: trailingSlash should be false")
    srcs = {r.get("source") for r in cfg.get("redirects", [])}
    for required in ("/home",):
        if required not in srcs:
            fail(f"vercel.json: missing legacy redirect for {required}")


def check_noindex_pages(pages):
    """Pages in NOINDEX_PAGES must exist and must carry a noindex robots tag."""
    present = {p for p, _ in pages}
    for name in NOINDEX_PAGES:
        if name not in present:
            fail(f"expected noindex page missing from {OUT}/ -> {name}")
    for p, html in pages:
        tags = re.findall(r'<meta name="robots" content="([^"]*)"', html)
        if p in NOINDEX_PAGES:
            if not tags:
                fail(f"{p}: expected a robots meta tag, found none")
            elif len(tags) > 1:
                fail(f"{p}: {len(tags)} competing robots tags")
            elif "noindex" not in tags[0]:
                fail(f"{p}: robots tag lost its noindex -> {tags[0]}")
        else:
            for t in tags:
                if "noindex" in t:
                    fail(f"{p}: unexpected noindex robots tag -> {t}")


def check_assets_resolve(pages):
    """Every local asset reference must exist on disk."""
    for p, html in pages:
        for url in re.findall(r'(?:src|href)="(/assets/[^"]*)"', html):
            fp = os.path.join(OUT, url.lstrip("/"))
            if not os.path.exists(fp):
                fail(f"{p}: asset not found -> {url}")


# ---------------------------------------------------------------- run
def main():
    files = page_files()
    if not files:
        print("FAIL: no HTML in site/")
        return 1
    pages = [(os.path.basename(f), read(f)) for f in files]

    check_placeholder_links(pages)
    check_noopener(pages)
    check_internal_links_extensionless(pages)
    check_titles_descriptions(pages)
    check_single_h1(pages)
    check_jsonld(pages)
    check_em_dashes(pages)
    check_canonicals(pages)
    check_sitemap(pages)
    check_vercel_config()
    check_noindex_pages(pages)
    check_assets_resolve(pages)

    print(f"verify: {len(pages)} pages checked")
    for n in notes:
        print(f"  note: {n}")
    if failures:
        print(f"\nFAILED ({len(failures)}):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
