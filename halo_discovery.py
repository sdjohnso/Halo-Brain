#!/usr/bin/env python3
"""
HaloPSA Documentation Discovery Crawler
========================================
Discovers every article URL on the HaloPSA guides portal, collects metadata
on each article, and produces halo_manifest.json, halo_manifest.csv, and
halo_errors.log.

Target: https://usehalo.com/halopsa/guides/
"""

import csv
import json
import logging
import re
import sys
import time
from collections import OrderedDict
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse, parse_qs

import requests
from bs4 import BeautifulSoup, Comment

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_URL = "https://usehalo.com/halopsa/guides/"
GUIDE_SINGLE_BASE = "https://usehalo.com/guide/"
FAQ_LIST_BASE = "https://usehalo.com/faq-list/"
LEGACY_BASE = "https://halopsa.com/guides/article/"

DELAY = 1.5  # seconds between requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}

MANIFEST_JSON = "halo_manifest.json"
MANIFEST_CSV = "halo_manifest.csv"
ERROR_LOG = "halo_errors.log"

# Known FAQ-list category slugs that contain HaloPSA guide articles.
# The crawler will also discover additional ones dynamically.
SEED_FAQ_CATEGORIES = [
    "halopsa-guides",
    "halopsa-academy",
    "halopsa-academy-halopsa-public-guides",
    "an-introduction-to-halopsa",
    "implementation-checklist",
    "email-configuration",
    "organisation",
    "ticket-rules",
    "viewing-tickets-and-lists",
    "customising-branding-halo",
    "service-catalogue-self-service-portal-using-and-configuring-halo",
    "portal-customisation-self-service-portal",
    "organization-multitenancy",
    "fields-database-lookups-categories",
    "service-desk-using-and-configuring-halo",
    "raising-tickets",
    "product-management",
    "tickets",
    "automation-tools-integrations-haloitsm-public-guides",
    "faqs",
    "halopsa-website",
    "rmm-device-management",
    "integrations",
    "accounting",
    "security-halocrm-public-guides",
    "haloitsm-public-guides",
    "haloitsm-trial-guides",
]

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
error_logger = logging.getLogger("halo_errors")
error_logger.setLevel(logging.WARNING)
_fh = logging.FileHandler(ERROR_LOG, mode="w", encoding="utf-8")
_fh.setFormatter(logging.Formatter("%(asctime)s  %(levelname)s  %(message)s"))
error_logger.addHandler(_fh)

console = logging.getLogger("halo_console")
console.setLevel(logging.INFO)
_ch = logging.StreamHandler(sys.stdout)
_ch.setFormatter(logging.Formatter("%(asctime)s  %(message)s"))
console.addHandler(_ch)

# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------
session = requests.Session()
session.headers.update(HEADERS)


def polite_get(url: str, retries: int = 3) -> requests.Response | None:
    """GET with polite delay and simple retry logic."""
    for attempt in range(retries):
        try:
            resp = session.get(url, timeout=30, allow_redirects=True)
            return resp
        except requests.RequestException as exc:
            console.warning(f"  Request error ({attempt+1}/{retries}): {url} -> {exc}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
    return None


def throttle():
    """Polite delay between requests."""
    time.sleep(DELAY)

# ---------------------------------------------------------------------------
# URL normalisation
# ---------------------------------------------------------------------------
def normalise_url(url: str) -> str:
    """Normalise a guide URL to its canonical usehalo.com form."""
    url = url.strip().rstrip("/")
    # Convert legacy halopsa.com URLs
    url = url.replace("https://halopsa.com/guides/article/", "https://usehalo.com/halopsa/guides/article/")
    url = url.replace("http://halopsa.com/guides/article/", "https://usehalo.com/halopsa/guides/article/")
    # Remove trailing slash inconsistency
    if not url.endswith("/"):
        parsed = urlparse(url)
        if not parsed.query:
            url += "/"
    return url


def is_article_url(url: str) -> bool:
    """Check if a URL looks like an individual guide/article page."""
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")

    # /guide/<slug>
    if re.match(r"^/guide/[a-z0-9][a-z0-9\-]+$", path, re.IGNORECASE):
        return True
    # /halopsa/guides/<numeric-id>
    if re.match(r"^/halopsa/guides/\d+$", path):
        return True
    # /halopsa/guides/article/?kbid=XXXX
    if "/guides/article" in path and "kbid" in parsed.query:
        return True
    return False


def is_faq_list_url(url: str) -> bool:
    """Check if a URL is an FAQ list category page."""
    parsed = urlparse(url)
    return parsed.path.startswith("/faq-list/")

# ---------------------------------------------------------------------------
# Phase 1a: Discovery — collect all article URLs
# ---------------------------------------------------------------------------
def discover_from_main_index(discovered: set[str]):
    """Parse the main guides index page for article links."""
    console.info("Fetching main guides index: %s", BASE_URL)
    resp = polite_get(BASE_URL)
    if resp is None or resp.status_code != 200:
        error_logger.error(f"Could not fetch main index: {BASE_URL} (status={getattr(resp, 'status_code', 'N/A')})")
        return

    soup = BeautifulSoup(resp.text, "lxml")
    _extract_article_links(soup, resp.url, discovered)
    _extract_faq_category_links(soup, resp.url)
    throttle()


def discover_from_faq_list(category_slug: str, discovered: set[str]):
    """Paginate through an /faq-list/<category>/ archive and collect links."""
    page = 1
    while True:
        if page == 1:
            url = f"{FAQ_LIST_BASE}{category_slug}/"
        else:
            url = f"{FAQ_LIST_BASE}{category_slug}/page/{page}/"

        console.info("  FAQ list: %s  (page %d)", category_slug, page)
        resp = polite_get(url)
        if resp is None or resp.status_code != 200:
            if page == 1:
                error_logger.warning(f"FAQ category not found: {url}")
            break

        soup = BeautifulSoup(resp.text, "lxml")
        before = len(discovered)
        _extract_article_links(soup, resp.url, discovered)

        # Check for next page
        has_next = False
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if f"/page/{page + 1}/" in href:
                has_next = True
                break
        # Also check for "next" rel link
        for link in soup.find_all("link", rel="next"):
            has_next = True
            break

        # Also look for any pagination nav with higher page numbers
        if not has_next:
            for a in soup.find_all("a", href=True):
                match = re.search(r"/page/(\d+)/", a["href"])
                if match and int(match.group(1)) > page:
                    has_next = True
                    break

        throttle()
        if not has_next:
            break
        page += 1

        # Safety: stop after 100 pages per category
        if page > 100:
            break


_discovered_faq_slugs: set[str] = set()


def _extract_faq_category_links(soup: BeautifulSoup, base_url: str):
    """Find links to /faq-list/ category pages for further crawling."""
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a["href"])
        parsed = urlparse(href)
        if parsed.netloc and "usehalo.com" not in parsed.netloc:
            continue
        match = re.match(r"^/faq-list/([a-z0-9\-]+)/?$", parsed.path, re.IGNORECASE)
        if match:
            slug = match.group(1)
            _discovered_faq_slugs.add(slug)


def _extract_article_links(soup: BeautifulSoup, base_url: str, discovered: set[str]):
    """Extract all article-like links from a parsed page."""
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a["href"])
        parsed = urlparse(href)
        # Only usehalo.com or halopsa.com
        if parsed.netloc and not any(d in parsed.netloc for d in ("usehalo.com", "halopsa.com")):
            continue
        if is_article_url(href):
            discovered.add(normalise_url(href))


def discover_from_sitemap(discovered: set[str]):
    """Attempt to parse XML sitemaps for additional URLs."""
    sitemap_urls = [
        "https://usehalo.com/sitemap.xml",
        "https://usehalo.com/sitemap_index.xml",
        "https://usehalo.com/wp-sitemap.xml",
        "https://usehalo.com/guide-sitemap.xml",
        "https://usehalo.com/wp-sitemap-posts-guide-1.xml",
    ]
    for surl in sitemap_urls:
        console.info("Checking sitemap: %s", surl)
        resp = polite_get(surl)
        if resp is None or resp.status_code != 200:
            continue
        # Parse XML sitemap
        try:
            soup = BeautifulSoup(resp.text, "lxml-xml")
        except Exception:
            soup = BeautifulSoup(resp.text, "lxml")

        # Look for <loc> tags
        for loc in soup.find_all("loc"):
            url = loc.get_text(strip=True)
            if is_article_url(url):
                discovered.add(normalise_url(url))
            # Nested sitemaps
            if url.endswith(".xml"):
                console.info("  Following nested sitemap: %s", url)
                nested = polite_get(url)
                if nested and nested.status_code == 200:
                    try:
                        nsoup = BeautifulSoup(nested.text, "lxml-xml")
                    except Exception:
                        nsoup = BeautifulSoup(nested.text, "lxml")
                    for nloc in nsoup.find_all("loc"):
                        nurl = nloc.get_text(strip=True)
                        if is_article_url(nurl):
                            discovered.add(normalise_url(nurl))
                throttle()
        throttle()


def brute_force_kbid_range(discovered: set[str], sample_ids: list[int] | None = None):
    """
    Optionally probe a range of kbid values to find articles not linked anywhere.
    This is conservative — we only probe IDs near known ones.
    """
    if sample_ids is None:
        # Known kbid values from research
        sample_ids = [1530, 1823, 2100, 2305, 2330, 2370, 2371]

    if not sample_ids:
        return

    min_id = min(sample_ids) - 50
    max_id = max(sample_ids) + 50
    min_id = max(1, min_id)

    console.info("Probing kbid range %d-%d for unlisted articles...", min_id, max_id)

    for kbid in range(min_id, max_id + 1):
        url = f"https://usehalo.com/halopsa/guides/article/?kbid={kbid}"
        normalised = normalise_url(url)
        if normalised in discovered:
            continue
        # We also check the /halopsa/guides/<id>/ pattern
        alt_url = f"https://usehalo.com/halopsa/guides/{kbid}/"
        if alt_url in discovered:
            continue

        resp = polite_get(url)
        if resp is None:
            continue
        if resp.status_code == 200:
            # Check that it's actually an article, not a "not found" page
            if "guide not found" not in resp.text.lower() and len(resp.text) > 2000:
                discovered.add(normalised)
                console.info("  Found unlisted article: kbid=%d", kbid)
        throttle()


# ---------------------------------------------------------------------------
# Phase 1b: Metadata extraction per article
# ---------------------------------------------------------------------------
BODY_STRIP_TAGS = {"nav", "footer", "header", "aside", "script", "style", "noscript"}
BODY_STRIP_CLASSES = {
    "sidebar", "navigation", "nav", "footer", "header", "menu",
    "breadcrumb", "widget", "comment", "social", "share",
}


def _get_body_soup(soup: BeautifulSoup) -> BeautifulSoup:
    """
    Return a copy of the soup with nav/footer/sidebar elements removed,
    leaving only the main article body content.
    """
    # Try to find the main content container
    main = (
        soup.find("article")
        or soup.find("main")
        or soup.find("div", class_=re.compile(r"(entry|content|article|guide|kb)", re.I))
        or soup.find("div", id=re.compile(r"(content|article|guide|main)", re.I))
    )
    if main is None:
        main = soup.find("body") or soup

    # Remove unwanted elements
    for tag_name in BODY_STRIP_TAGS:
        for el in main.find_all(tag_name):
            el.decompose()
    for el in main.find_all(True, class_=True):
        classes = " ".join(el.get("class", []))
        if any(c in classes.lower() for c in BODY_STRIP_CLASSES):
            el.decompose()
    # Remove HTML comments
    for comment in main.find_all(string=lambda t: isinstance(t, Comment)):
        comment.extract()
    return main


def extract_metadata(url: str) -> dict | None:
    """Fetch a single article URL and extract metadata."""
    resp = polite_get(url)
    if resp is None:
        error_logger.error(f"Connection failed: {url}")
        return None

    status = resp.status_code
    final_url = resp.url

    # Check for redirect to non-article page
    if status in (301, 302, 303, 307, 308):
        error_logger.warning(f"Redirect {status}: {url} -> {final_url}")
    if status == 404:
        error_logger.warning(f"404 Not Found: {url}")
        return None
    if status != 200:
        error_logger.warning(f"HTTP {status}: {url}")
        return None

    soup = BeautifulSoup(resp.text, "lxml")

    # Check for "guide not found" placeholder pages
    body_text_lower = soup.get_text(separator=" ", strip=True).lower()
    if "guide not found" in body_text_lower and len(resp.text) < 5000:
        error_logger.warning(f"Guide not found page: {url}")
        return None

    # Title
    h1 = soup.find("h1")
    title_tag = soup.find("title")
    title = ""
    if h1:
        title = h1.get_text(strip=True)
    elif title_tag:
        title = title_tag.get_text(strip=True)

    # All headings
    headings = OrderedDict()
    for level in ("h1", "h2", "h3", "h4"):
        tags = soup.find_all(level)
        if tags:
            headings[level] = [t.get_text(strip=True) for t in tags]

    # Body content (stripped of nav/footer/sidebar)
    body = _get_body_soup(BeautifulSoup(resp.text, "lxml"))
    body_text = body.get_text(separator=" ", strip=True)
    words = body_text.split()
    word_count = len(words)
    est_tokens = int(word_count * 1.35)

    # Images
    images = body.find_all("img")
    image_count = len(images)

    # Code blocks
    code_blocks = body.find_all(["pre", "code"])
    code_block_count = len(code_blocks)

    # Lists
    has_ordered_list = len(body.find_all("ol")) > 0
    has_unordered_list = len(body.find_all("ul")) > 0
    has_lists = has_ordered_list or has_unordered_list

    # Last-Modified header
    last_modified = resp.headers.get("Last-Modified", "")

    # Detect section/category from breadcrumb or page structure
    section = ""
    breadcrumb = soup.find(class_=re.compile(r"breadcrumb", re.I))
    if breadcrumb:
        crumbs = breadcrumb.find_all("a")
        if len(crumbs) >= 2:
            section = crumbs[-1].get_text(strip=True)

    # Also try to detect from faq-list category
    if not section:
        for a in soup.find_all("a", href=True):
            href = a["href"]
            match = re.search(r"/faq-list/([a-z0-9\-]+)/?$", href, re.I)
            if match:
                section = match.group(1).replace("-", " ").title()
                break

    return {
        "url": url,
        "final_url": final_url,
        "title": title,
        "section": section,
        "headings": dict(headings),
        "word_count": word_count,
        "estimated_tokens": est_tokens,
        "image_count": image_count,
        "code_block_count": code_block_count,
        "has_ordered_list": has_ordered_list,
        "has_unordered_list": has_unordered_list,
        "has_lists": has_lists,
        "http_status": status,
        "last_modified": last_modified,
    }


# ---------------------------------------------------------------------------
# Phase 1c: Save results
# ---------------------------------------------------------------------------
CSV_COLUMNS = [
    "url", "final_url", "title", "section", "word_count", "estimated_tokens",
    "image_count", "code_block_count", "has_ordered_list", "has_unordered_list",
    "has_lists", "http_status", "last_modified",
    "h1_count", "h2_count", "h3_count", "h4_count",
]


def save_manifest(articles: list[dict]):
    """Save to JSON and CSV."""
    # JSON
    with open(MANIFEST_JSON, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)
    console.info("Saved %d articles to %s", len(articles), MANIFEST_JSON)

    # CSV
    with open(MANIFEST_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for art in articles:
            row = dict(art)
            headings = art.get("headings", {})
            row["h1_count"] = len(headings.get("h1", []))
            row["h2_count"] = len(headings.get("h2", []))
            row["h3_count"] = len(headings.get("h3", []))
            row["h4_count"] = len(headings.get("h4", []))
            writer.writerow(row)
    console.info("Saved %d articles to %s", len(articles), MANIFEST_CSV)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    console.info("=" * 60)
    console.info("HaloPSA Discovery Crawler — %s", datetime.now(timezone.utc).isoformat())
    console.info("=" * 60)

    discovered: set[str] = set()

    # Step 1: Main index
    console.info("\n--- Step 1: Main guides index ---")
    discover_from_main_index(discovered)
    console.info("  URLs after main index: %d", len(discovered))

    # Step 2: Sitemap
    console.info("\n--- Step 2: Sitemaps ---")
    discover_from_sitemap(discovered)
    console.info("  URLs after sitemaps: %d", len(discovered))

    # Step 3: FAQ-list category archives
    console.info("\n--- Step 3: FAQ-list category archives ---")
    all_slugs = set(SEED_FAQ_CATEGORIES) | _discovered_faq_slugs
    console.info("  Categories to crawl: %d", len(all_slugs))
    for slug in sorted(all_slugs):
        discover_from_faq_list(slug, discovered)
    console.info("  URLs after FAQ lists: %d", len(discovered))

    # Step 4: Brute-force kbid probe (optional, near known IDs)
    console.info("\n--- Step 4: kbid range probe ---")
    brute_force_kbid_range(discovered)
    console.info("  URLs after kbid probe: %d", len(discovered))

    # Deduplicate and sort
    discovered = {normalise_url(u) for u in discovered}
    url_list = sorted(discovered)
    console.info("\n--- Total unique article URLs discovered: %d ---", len(url_list))

    # Step 5: Fetch metadata for each article
    console.info("\n--- Step 5: Fetching metadata for each article ---")
    articles = []
    errors = 0
    for i, url in enumerate(url_list, 1):
        console.info("  [%d/%d] %s", i, len(url_list), url)
        meta = extract_metadata(url)
        if meta:
            articles.append(meta)
        else:
            errors += 1
        throttle()

    console.info("\n--- Metadata collection complete ---")
    console.info("  Successful: %d", len(articles))
    console.info("  Errors/Skipped: %d", errors)

    # Step 6: Save
    save_manifest(articles)

    console.info("\nDone. See %s, %s, and %s", MANIFEST_JSON, MANIFEST_CSV, ERROR_LOG)


if __name__ == "__main__":
    main()
