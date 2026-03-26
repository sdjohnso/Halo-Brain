#!/usr/bin/env python3
"""
HaloPSA Content Extraction & Chunking Pipeline
=================================================
Full pipeline that:
  1. Reads the article manifest (halo_manifest.json)
  2. Fetches each article's HTML content (with polite delays)
  3. Extracts clean article body content
  4. Chunks using heading-based structural chunking with fixed-token fallback
  5. Outputs vector-store-ready chunks to halo_chunks.jsonl and halo_chunks.json

Usage:
  python halo_extract_and_chunk.py                    # Full pipeline
  python halo_extract_and_chunk.py --from-manifest     # Chunk from manifest estimates (no HTTP)
  python halo_extract_and_chunk.py --from-html-dir DIR # Chunk from pre-downloaded HTML files

The --from-manifest mode uses word counts and heading data already in the manifest
to generate synthetic-but-structurally-realistic chunks. This is useful when direct
HTTP access is unavailable.
"""

import argparse
import csv
import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from halo_chunker import (
    Chunk,
    chunk_article,
    chunk_plain_text,
    extract_article_body,
    get_structured_text,
    estimate_tokens,
    word_count,
    MAX_CHUNK_TOKENS,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MANIFEST_JSON = "halo_manifest.json"
CHUNKS_JSONL = "halo_chunks.jsonl"
CHUNKS_JSON = "halo_chunks.json"
CHUNKS_CSV = "halo_chunks_summary.csv"
CHUNK_LOG = "halo_chunking.log"
RAW_HTML_DIR = "halo_raw_html"

DELAY = 1.5  # seconds between HTTP requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("halo_pipeline")
logger.setLevel(logging.INFO)
_ch = logging.StreamHandler(sys.stdout)
_ch.setFormatter(logging.Formatter("%(asctime)s  %(message)s"))
logger.addHandler(_ch)
_fh = logging.FileHandler(CHUNK_LOG, mode="w", encoding="utf-8")
_fh.setFormatter(logging.Formatter("%(asctime)s  %(levelname)s  %(message)s"))
logger.addHandler(_fh)

# ---------------------------------------------------------------------------
# HTTP fetch
# ---------------------------------------------------------------------------
session = requests.Session()
session.headers.update(HEADERS)


def fetch_article_html(url: str) -> str | None:
    """Fetch article HTML with retry logic."""
    for attempt in range(3):
        try:
            resp = session.get(url, timeout=30, allow_redirects=True)
            if resp.status_code == 200:
                return resp.text
            elif resp.status_code == 404:
                logger.warning("  404: %s", url)
                return None
            else:
                logger.warning("  HTTP %d: %s (attempt %d)", resp.status_code, url, attempt + 1)
        except requests.RequestException as exc:
            logger.warning("  Request error: %s (attempt %d)", exc, attempt + 1)
        if attempt < 2:
            time.sleep(2 ** attempt)
    return None


def save_raw_html(url: str, html: str, output_dir: str):
    """Save raw HTML to disk for caching/debugging."""
    os.makedirs(output_dir, exist_ok=True)
    # Create filename from URL
    slug = re.sub(r"[^a-zA-Z0-9]", "_", url)[-120:]
    filepath = os.path.join(output_dir, f"{slug}.html")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)


# ---------------------------------------------------------------------------
# Mode 1: Full pipeline (fetch + chunk)
# ---------------------------------------------------------------------------
def run_full_pipeline(manifest: list[dict]) -> list[dict]:
    """Fetch each article and chunk it."""
    all_chunks = []

    for i, article in enumerate(manifest, 1):
        url = article["url"]
        title = article.get("title", "")
        section = article.get("section", "Uncategorized")

        logger.info("[%d/%d] Fetching: %s", i, len(manifest), url)

        html = fetch_article_html(url)
        if html is None:
            logger.warning("  Skipped: could not fetch")
            continue

        # Cache raw HTML
        save_raw_html(url, html, RAW_HTML_DIR)

        # Chunk the article
        try:
            chunks = chunk_article(url, title, section, html)
            all_chunks.extend(c.to_dict() for c in chunks)
            logger.info("  -> %d chunks (total words: %d)", len(chunks),
                       sum(c.word_count for c in chunks))
        except Exception as exc:
            logger.error("  Chunking error: %s — %s", url, exc)

        time.sleep(DELAY)

    return all_chunks


# ---------------------------------------------------------------------------
# Mode 2: From pre-downloaded HTML directory
# ---------------------------------------------------------------------------
def run_from_html_dir(manifest: list[dict], html_dir: str) -> list[dict]:
    """Chunk from pre-downloaded HTML files."""
    all_chunks = []

    for i, article in enumerate(manifest, 1):
        url = article["url"]
        title = article.get("title", "")
        section = article.get("section", "Uncategorized")

        # Find matching HTML file
        slug = re.sub(r"[^a-zA-Z0-9]", "_", url)[-120:]
        filepath = os.path.join(html_dir, f"{slug}.html")

        if not os.path.exists(filepath):
            logger.warning("[%d/%d] No HTML file for: %s", i, len(manifest), url)
            continue

        logger.info("[%d/%d] Processing: %s", i, len(manifest), title or url)

        with open(filepath, "r", encoding="utf-8") as f:
            html = f.read()

        try:
            chunks = chunk_article(url, title, section, html)
            all_chunks.extend(c.to_dict() for c in chunks)
            logger.info("  -> %d chunks", len(chunks))
        except Exception as exc:
            logger.error("  Chunking error: %s — %s", url, exc)

    return all_chunks


# ---------------------------------------------------------------------------
# Mode 3: From manifest only (synthetic content from metadata)
# ---------------------------------------------------------------------------
def run_from_manifest(manifest: list[dict]) -> list[dict]:
    """
    Generate chunks from manifest metadata alone (no HTML fetching).
    Uses word counts and heading structures from the manifest to produce
    structurally representative chunks. The chunk text is a placeholder
    that preserves the structural shape (heading + section pattern).

    This mode is useful for:
    - Testing the chunking pipeline
    - Estimating chunk counts before full extraction
    - Working in restricted network environments
    """
    all_chunks = []

    for i, article in enumerate(manifest, 1):
        url = article["url"]
        title = article.get("title", "")
        section = article.get("section", "Uncategorized")
        headings = article.get("headings", {})
        target_words = article.get("word_count", 500)

        logger.info("[%d/%d] Chunking (manifest mode): %s", i, len(manifest), title or url)

        # Generate synthetic content that matches the manifest metadata
        text = _generate_representative_text(title, section, headings, target_words)

        # Chunk using the plain-text chunker with heading info
        chunks = chunk_plain_text(url, title, section, text, headings)
        all_chunks.extend(c.to_dict() for c in chunks)

        if chunks:
            logger.info("  -> %d chunks (est. tokens: %d)",
                       len(chunks), sum(c.estimated_tokens for c in chunks))

    return all_chunks


def _generate_representative_text(
    title: str,
    section: str,
    headings: dict,
    target_words: int,
) -> str:
    """
    Generate placeholder text that structurally matches the article.
    The text preserves heading structure and approximate word count.
    """
    h2_list = headings.get("h2", [])
    h3_list = headings.get("h3", [])

    parts = []

    if not h2_list:
        # Flat article — generate a single block of text
        parts.append(_placeholder_paragraph(title, section, target_words))
    else:
        # Intro paragraph (10% of words)
        intro_words = max(30, int(target_words * 0.1))
        parts.append(_placeholder_paragraph(
            f"This guide covers {title.lower()} in {section}.",
            section, intro_words
        ))

        # Distribute remaining words across H2 sections
        remaining_words = target_words - intro_words
        words_per_h2 = max(50, remaining_words // len(h2_list)) if h2_list else remaining_words

        h3_idx = 0
        for h2_heading in h2_list:
            parts.append(f"\n\n{h2_heading}\n")

            # Check if this H2 section has H3 subsections
            # Distribute H3s roughly evenly across H2s
            h3_per_h2 = len(h3_list) // len(h2_list) if h2_list else 0
            section_h3s = h3_list[h3_idx:h3_idx + h3_per_h2] if h3_per_h2 > 0 else []
            h3_idx += h3_per_h2

            if section_h3s:
                words_per_h3 = max(30, words_per_h2 // len(section_h3s))
                for h3_heading in section_h3s:
                    parts.append(f"\n{h3_heading}\n")
                    parts.append(_placeholder_paragraph(h3_heading, section, words_per_h3))
            else:
                parts.append(_placeholder_paragraph(h2_heading, section, words_per_h2))

    return "\n".join(parts)


def _placeholder_paragraph(context: str, section: str, target_words: int) -> str:
    """Generate a representative placeholder paragraph."""
    # Use varied sentence templates to create realistic-looking content
    templates = [
        f"This section covers the configuration and setup of {context.lower()} within HaloPSA.",
        f"To configure this feature, navigate to Configuration in the admin panel.",
        f"The {section} module provides several options for customization.",
        f"Follow these steps to complete the setup process for your organization.",
        f"This guide explains how to use and configure the relevant settings.",
        f"Review the settings below and adjust them according to your requirements.",
        f"For more information about related features, see the linked guides.",
        f"The configuration options are found under the Settings tab.",
        f"Administrators can manage these settings from the Configuration console.",
        f"This feature is available for all subscription tiers in HaloPSA.",
        f"Changes to these settings take effect immediately after saving.",
        f"You can customize the behavior by modifying the relevant fields.",
        f"The system provides default values that work for most organizations.",
        f"Advanced users can configure additional options in the General Settings area.",
        f"Contact support if you need assistance with this configuration.",
    ]

    lines = []
    current_words = 0
    idx = 0

    while current_words < target_words:
        line = templates[idx % len(templates)]
        lines.append(line)
        current_words += len(line.split())
        idx += 1

        # Avoid infinite loop
        if idx > target_words:
            break

    return " ".join(lines)


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
def save_chunks(chunks: list[dict]):
    """Save chunks in multiple formats."""
    # JSONL (streaming format — one chunk per line)
    with open(CHUNKS_JSONL, "w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    logger.info("Saved %d chunks to %s", len(chunks), CHUNKS_JSONL)

    # JSON (full array)
    with open(CHUNKS_JSON, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
    logger.info("Saved %d chunks to %s", len(chunks), CHUNKS_JSON)

    # Summary CSV
    csv_cols = [
        "chunk_id", "article_url", "article_title", "section_category",
        "chunk_index", "total_chunks_in_article", "word_count",
        "estimated_tokens", "chunk_type", "has_code", "has_list",
        "heading_breadcrumb",
    ]
    with open(CHUNKS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=csv_cols, extrasaction="ignore")
        writer.writeheader()
        for chunk in chunks:
            row = dict(chunk)
            row["heading_breadcrumb"] = " > ".join(chunk.get("heading_breadcrumb", []))
            writer.writerow(row)
    logger.info("Saved chunk summary to %s", CHUNKS_CSV)


def print_stats(chunks: list[dict]):
    """Print chunking statistics."""
    if not chunks:
        logger.info("No chunks produced.")
        return

    total = len(chunks)
    total_words = sum(c["word_count"] for c in chunks)
    total_tokens = sum(c["estimated_tokens"] for c in chunks)
    avg_tokens = total_tokens / total
    articles = len(set(c["article_url"] for c in chunks))

    # Chunk type distribution
    type_counts = {}
    for c in chunks:
        t = c["chunk_type"]
        type_counts[t] = type_counts.get(t, 0) + 1

    # Token distribution
    token_vals = [c["estimated_tokens"] for c in chunks]
    token_vals.sort()
    p25 = token_vals[total // 4] if total >= 4 else token_vals[0]
    p50 = token_vals[total // 2]
    p75 = token_vals[3 * total // 4] if total >= 4 else token_vals[-1]
    p95 = token_vals[int(total * 0.95)] if total >= 20 else token_vals[-1]

    logger.info("")
    logger.info("=" * 60)
    logger.info("CHUNKING STATISTICS")
    logger.info("=" * 60)
    logger.info("  Articles processed:     %d", articles)
    logger.info("  Total chunks produced:   %d", total)
    logger.info("  Avg chunks per article:  %.1f", total / articles if articles else 0)
    logger.info("  Total words in chunks:   %s", f"{total_words:,}")
    logger.info("  Total tokens in chunks:  %s", f"{total_tokens:,}")
    logger.info("  Avg tokens per chunk:    %.0f", avg_tokens)
    logger.info("")
    logger.info("  Token distribution:")
    logger.info("    p25: %d  p50: %d  p75: %d  p95: %d", p25, p50, p75, p95)
    logger.info("    min: %d  max: %d", token_vals[0], token_vals[-1])
    logger.info("")
    logger.info("  Chunk type breakdown:")
    for ctype, count in sorted(type_counts.items()):
        pct = count / total * 100
        logger.info("    %-20s %4d  (%5.1f%%)", ctype, count, pct)
    logger.info("")

    # Content signals
    with_code = sum(1 for c in chunks if c.get("has_code"))
    with_list = sum(1 for c in chunks if c.get("has_list"))
    with_images = sum(1 for c in chunks if c.get("has_image_refs"))
    logger.info("  Content signals in chunks:")
    logger.info("    With code:   %d (%.1f%%)", with_code, with_code / total * 100)
    logger.info("    With lists:  %d (%.1f%%)", with_list, with_list / total * 100)
    logger.info("    With images: %d (%.1f%%)", with_images, with_images / total * 100)
    logger.info("=" * 60)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="HaloPSA Content Extraction & Chunking Pipeline"
    )
    parser.add_argument(
        "--from-manifest", action="store_true",
        help="Generate chunks from manifest metadata only (no HTTP fetching)"
    )
    parser.add_argument(
        "--from-html-dir", type=str, default=None,
        help="Chunk from pre-downloaded HTML files in the given directory"
    )
    parser.add_argument(
        "--manifest", type=str, default=MANIFEST_JSON,
        help=f"Path to manifest JSON file (default: {MANIFEST_JSON})"
    )
    args = parser.parse_args()

    # Load manifest
    logger.info("=" * 60)
    logger.info("HaloPSA Content Extraction & Chunking Pipeline")
    logger.info("Started: %s", datetime.now(timezone.utc).isoformat())
    logger.info("=" * 60)

    try:
        with open(args.manifest, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except FileNotFoundError:
        logger.error("Manifest not found: %s", args.manifest)
        logger.error("Run halo_discovery.py or halo_bootstrap_manifest.py first.")
        sys.exit(1)

    logger.info("Loaded manifest: %d articles", len(manifest))
    logger.info("Chunking config: max_tokens=%d, overlap=%d",
               MAX_CHUNK_TOKENS, 50)

    # Run appropriate mode
    if args.from_manifest:
        logger.info("Mode: from-manifest (synthetic content, structural shape preserved)")
        chunks = run_from_manifest(manifest)
    elif args.from_html_dir:
        logger.info("Mode: from-html-dir (%s)", args.from_html_dir)
        chunks = run_from_html_dir(manifest, args.from_html_dir)
    else:
        logger.info("Mode: full pipeline (fetch + chunk)")
        chunks = run_full_pipeline(manifest)

    # Save and report
    save_chunks(chunks)
    print_stats(chunks)

    logger.info("\nDone. Files written:")
    logger.info("  %s  — JSONL (one chunk per line, for streaming ingestion)", CHUNKS_JSONL)
    logger.info("  %s   — JSON array (for inspection)", CHUNKS_JSON)
    logger.info("  %s — CSV summary (for spreadsheet review)", CHUNKS_CSV)


if __name__ == "__main__":
    main()
