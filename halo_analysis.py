#!/usr/bin/env python3
"""
HaloPSA Documentation Analysis Report Generator
=================================================
Reads halo_manifest.json and produces halo_report.md with comprehensive
statistics, distribution analysis, structural depth analysis, content type
signals, chunking recommendations, and section breakdowns.
"""

import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

MANIFEST_JSON = "halo_manifest.json"
REPORT_MD = "halo_report.md"


def load_manifest() -> list[dict]:
    with open(MANIFEST_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def fmt(n: int | float) -> str:
    """Format a number with commas."""
    if isinstance(n, float):
        return f"{n:,.1f}"
    return f"{n:,}"


def generate_report(articles: list[dict]) -> str:
    lines: list[str] = []

    def h1(text):
        lines.append(f"# {text}\n")

    def h2(text):
        lines.append(f"## {text}\n")

    def h3(text):
        lines.append(f"### {text}\n")

    def p(text=""):
        lines.append(f"{text}\n")

    def row(cols, widths=None):
        if widths:
            cells = [str(c).ljust(w) for c, w in zip(cols, widths)]
        else:
            cells = [str(c) for c in cols]
        lines.append("| " + " | ".join(cells) + " |")

    def sep(n):
        lines.append("| " + " | ".join(["---"] * n) + " |")

    # -----------------------------------------------------------------------
    h1("HaloPSA Documentation Corpus — Discovery Analysis Report")
    p(f"*Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*")
    p(f"*Source: https://usehalo.com/halopsa/guides/*")
    p()

    total_articles = len(articles)
    total_words = sum(a["word_count"] for a in articles)
    total_tokens = sum(a["estimated_tokens"] for a in articles)
    chunks_400 = math.ceil(total_tokens / 400)
    # 500-token chunks with 50-token overlap: effective step = 450
    chunks_500_overlap = math.ceil(total_tokens / 450) if total_tokens else 0

    avg_words = total_words / total_articles if total_articles else 0
    median_words = sorted(a["word_count"] for a in articles)[total_articles // 2] if total_articles else 0

    # -----------------------------------------------------------------------
    h2("1. Summary Statistics")
    p()
    row(["Metric", "Value"])
    sep(2)
    row(["Total articles discovered", fmt(total_articles)])
    row(["Total word count", fmt(total_words)])
    row(["Total estimated token count", fmt(total_tokens)])
    row(["Average words per article", fmt(avg_words)])
    row(["Median words per article", fmt(median_words)])
    row(["Est. chunks (400-token structural)", fmt(chunks_400)])
    row(["Est. chunks (500-token fixed, 50-token overlap)", fmt(chunks_500_overlap)])
    p()

    # -----------------------------------------------------------------------
    h2("2. Content Distribution")
    p()

    # Histogram buckets
    buckets = [
        ("Under 200 words", 0, 200),
        ("200–500 words", 200, 500),
        ("500–1,000 words", 500, 1000),
        ("1,000–2,000 words", 1000, 2000),
        ("Over 2,000 words", 2000, float("inf")),
    ]

    h3("2a. Article Length Distribution")
    p()
    row(["Bucket", "Count", "% of Total"])
    sep(3)
    for label, lo, hi in buckets:
        count = sum(1 for a in articles if lo <= a["word_count"] < hi)
        pct = (count / total_articles * 100) if total_articles else 0
        bar = "█" * int(pct / 2)
        row([label, fmt(count), f"{pct:.1f}%  {bar}"])
    p()

    # Top 10 longest
    h3("2b. Top 10 Longest Articles (by word count)")
    p()
    sorted_by_len = sorted(articles, key=lambda a: a["word_count"], reverse=True)
    row(["#", "Words", "Tokens", "Title", "URL"])
    sep(5)
    for i, a in enumerate(sorted_by_len[:10], 1):
        title = a["title"][:60] or "(no title)"
        row([i, fmt(a["word_count"]), fmt(a["estimated_tokens"]), title, a["url"]])
    p()

    # Top 10 shortest (potential merge candidates)
    h3("2c. Top 10 Shortest Articles (potential merge candidates)")
    p()
    sorted_by_short = sorted(articles, key=lambda a: a["word_count"])
    row(["#", "Words", "Tokens", "Title", "URL"])
    sep(5)
    for i, a in enumerate(sorted_by_short[:10], 1):
        title = a["title"][:60] or "(no title)"
        row([i, fmt(a["word_count"]), fmt(a["estimated_tokens"]), title, a["url"]])
    p()

    # -----------------------------------------------------------------------
    h2("3. Structural Depth Analysis")
    p()
    p("This section analyses heading usage to determine whether structural/heading-based chunking is viable.")
    p()

    has_h2 = [a for a in articles if len(a.get("headings", {}).get("h2", [])) > 0]
    has_h3_plus = [a for a in articles if len(a.get("headings", {}).get("h3", [])) > 0 or len(a.get("headings", {}).get("h4", [])) > 0]
    flat = [a for a in articles if len(a.get("headings", {}).get("h2", [])) == 0]

    h2_counts = [len(a.get("headings", {}).get("h2", [])) for a in articles]
    avg_h2 = sum(h2_counts) / len(h2_counts) if h2_counts else 0
    max_h2 = max(h2_counts) if h2_counts else 0

    row(["Metric", "Count", "% of Total"])
    sep(3)
    row(["Articles with H2 headings (multi-section)", len(has_h2), f"{len(has_h2)/total_articles*100:.1f}%" if total_articles else "0%"])
    row(["Articles with H3+ headings (complex nested)", len(has_h3_plus), f"{len(has_h3_plus)/total_articles*100:.1f}%" if total_articles else "0%"])
    row(["Articles with no sub-headings (flat content)", len(flat), f"{len(flat)/total_articles*100:.1f}%" if total_articles else "0%"])
    p()

    row(["Metric", "Value"])
    sep(2)
    row(["Average H2 sections per article", f"{avg_h2:.1f}"])
    row(["Maximum H2 sections in one article", fmt(max_h2)])
    p()

    # Distribution of H2 counts
    h3("3a. H2 Heading Count Distribution")
    p()
    h2_dist = Counter(len(a.get("headings", {}).get("h2", [])) for a in articles)
    row(["H2 Count", "Articles"])
    sep(2)
    for count in sorted(h2_dist.keys()):
        label = f"{count}" if count < 20 else f"{count}+"
        row([label, fmt(h2_dist[count])])
    p()

    # -----------------------------------------------------------------------
    h2("4. Content Type Signals")
    p()

    with_code = [a for a in articles if a.get("code_block_count", 0) > 0]
    with_ol = [a for a in articles if a.get("has_ordered_list", False)]
    with_images = [a for a in articles if a.get("image_count", 0) > 0]
    with_ul = [a for a in articles if a.get("has_unordered_list", False)]

    row(["Content Signal", "Count", "% of Total"])
    sep(3)
    row(["Articles with code blocks (API/technical)", len(with_code), f"{len(with_code)/total_articles*100:.1f}%" if total_articles else "0%"])
    row(["Articles with numbered lists (procedural)", len(with_ol), f"{len(with_ol)/total_articles*100:.1f}%" if total_articles else "0%"])
    row(["Articles with bullet lists", len(with_ul), f"{len(with_ul)/total_articles*100:.1f}%" if total_articles else "0%"])
    row(["Articles with images", len(with_images), f"{len(with_images)/total_articles*100:.1f}%" if total_articles else "0%"])
    p()

    # Image distribution
    total_images = sum(a.get("image_count", 0) for a in articles)
    avg_images = total_images / total_articles if total_articles else 0
    p(f"**Total images across corpus:** {fmt(total_images)}")
    p(f"**Average images per article:** {avg_images:.1f}")
    p()

    # -----------------------------------------------------------------------
    h2("5. Chunking Recommendation")
    p()

    pct_with_h2 = len(has_h2) / total_articles * 100 if total_articles else 0
    pct_flat = len(flat) / total_articles * 100 if total_articles else 0
    pct_deep = len(has_h3_plus) / total_articles * 100 if total_articles else 0

    p("### Data-Driven Assessment")
    p()

    if pct_with_h2 >= 60:
        p(f"**{pct_with_h2:.0f}% of articles use H2 headings**, indicating strong structural markup "
          f"across the majority of the corpus. This makes **heading-based structural chunking** a "
          f"viable primary strategy.")
    elif pct_with_h2 >= 30:
        p(f"**{pct_with_h2:.0f}% of articles use H2 headings** — a moderate level of structural "
          f"markup. A **hybrid approach** is recommended.")
    else:
        p(f"Only **{pct_with_h2:.0f}% of articles use H2 headings**. Most content is flat. "
          f"**Fixed-token chunking** is the recommended primary strategy.")

    p()

    if pct_flat > 30:
        p(f"**{pct_flat:.0f}% of articles are flat** (no sub-headings). These articles will need "
          f"a fallback strategy — either treated as single chunks (if short enough) or split using "
          f"fixed-token windowing.")
    p()

    p("### Recommended Strategy")
    p()

    if pct_with_h2 >= 50:
        p("**Primary: Heading-based structural chunking with fixed-token fallback**")
        p()
        p("1. **For articles with H2+ headings:** Split on H2 boundaries. Each H2 section becomes "
          "a chunk. If a section exceeds 500 tokens, sub-split on H3 boundaries or use fixed-token "
          "windowing within the section.")
        p("2. **For flat articles under 500 tokens:** Keep as a single chunk.")
        p("3. **For flat articles over 500 tokens:** Use fixed-token chunking with 500-token windows "
          "and 50-token overlap.")
        p("4. **Metadata enrichment:** Attach article title, section/category, and URL to every chunk "
          "for retrieval context.")
    else:
        p("**Primary: Fixed-token chunking with structural enhancement where available**")
        p()
        p("1. **Default:** 500-token fixed windows with 50-token overlap.")
        p("2. **Where headings exist:** Prefer splitting on heading boundaries to preserve semantic coherence.")
        p("3. **Short articles (< 400 tokens):** Keep as single chunks.")
        p("4. **Metadata enrichment:** Attach article title, section/category, and URL to every chunk.")

    p()
    p(f"**Estimated total chunks:** {fmt(chunks_400)} (at 400-token structural) "
      f"to {fmt(chunks_500_overlap)} (at 500-token fixed with overlap)")
    p()

    # Short article merge candidates
    very_short = [a for a in articles if a["word_count"] < 100]
    if very_short:
        p(f"**Note:** {len(very_short)} articles have fewer than 100 words. Consider merging these "
          f"with related articles or treating them as metadata-only entries rather than standalone chunks.")
    p()

    # -----------------------------------------------------------------------
    h2("6. Section / Category Breakdown")
    p()

    sections: dict[str, list[dict]] = defaultdict(list)
    for a in articles:
        sec = a.get("section", "").strip() or "Uncategorized"
        sections[sec].append(a)

    row(["Section / Category", "Articles", "Total Words", "Avg Words"])
    sep(4)
    for sec in sorted(sections.keys()):
        arts = sections[sec]
        total_w = sum(a["word_count"] for a in arts)
        avg_w = total_w / len(arts) if arts else 0
        row([sec, fmt(len(arts)), fmt(total_w), fmt(avg_w)])
    p()

    # -----------------------------------------------------------------------
    h2("7. Data Quality Notes")
    p()
    # Check for duplicates by title
    title_counts = Counter(a["title"] for a in articles if a["title"])
    dupes = {t: c for t, c in title_counts.items() if c > 1}
    if dupes:
        p(f"**Potential duplicate titles found:** {len(dupes)}")
        for title, count in sorted(dupes.items(), key=lambda x: -x[1])[:10]:
            p(f"- \"{title}\" appears {count} times")
    else:
        p("No duplicate titles detected.")
    p()

    # Articles with no title
    no_title = [a for a in articles if not a.get("title", "").strip()]
    if no_title:
        p(f"**Articles with no title:** {len(no_title)}")
        for a in no_title[:5]:
            p(f"- {a['url']}")
    p()

    # Redirected articles
    redirected = [a for a in articles if a.get("url") != a.get("final_url")]
    if redirected:
        p(f"**Redirected URLs:** {len(redirected)}")
        for a in redirected[:5]:
            p(f"- {a['url']} → {a['final_url']}")
    p()

    p("---")
    p(f"*Report generated from {MANIFEST_JSON} containing {fmt(total_articles)} articles.*")

    return "\n".join(lines)


def main():
    try:
        articles = load_manifest()
    except FileNotFoundError:
        print(f"ERROR: {MANIFEST_JSON} not found. Run halo_discovery.py first.", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as exc:
        print(f"ERROR: Invalid JSON in {MANIFEST_JSON}: {exc}", file=sys.stderr)
        sys.exit(1)

    if not articles:
        print(f"WARNING: {MANIFEST_JSON} contains 0 articles.", file=sys.stderr)

    report = generate_report(articles)

    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"Report saved to {REPORT_MD}")
    print(f"  Articles analysed: {len(articles)}")
    print(f"  Total words: {sum(a['word_count'] for a in articles):,}")
    print(f"  Total est. tokens: {sum(a['estimated_tokens'] for a in articles):,}")


if __name__ == "__main__":
    main()
