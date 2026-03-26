#!/usr/bin/env python3
"""
HaloPSA Structural Chunker
============================
Implements heading-based structural chunking with fixed-token fallback,
as recommended by the discovery analysis report.

Strategy:
  1. Articles with H2+ headings: split on H2 boundaries. Each H2 section
     becomes a chunk. If a section exceeds MAX_CHUNK_TOKENS, sub-split on
     H3 boundaries or fall back to fixed-token windowing.
  2. Flat articles under MAX_CHUNK_TOKENS: keep as a single chunk.
  3. Flat articles over MAX_CHUNK_TOKENS: fixed-token windowing with overlap.
  4. Every chunk gets metadata: article title, section/category, URL,
     heading breadcrumb, chunk index, and position context.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field, asdict
from typing import Optional

from bs4 import BeautifulSoup, NavigableString, Tag, Comment

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MAX_CHUNK_TOKENS = 500        # Target max tokens per chunk
OVERLAP_TOKENS = 50           # Overlap for fixed-token windowing
TOKENS_PER_WORD = 1.35        # Approximation factor
MIN_CHUNK_WORDS = 30          # Discard chunks shorter than this
HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Chunk:
    """A single chunk ready for vector store ingestion."""
    chunk_id: str                     # Deterministic hash ID
    article_url: str                  # Source article URL
    article_title: str                # Article-level title
    section_category: str             # Category/section the article belongs to
    heading_breadcrumb: list[str]     # e.g. ["Asset Management", "Importing Assets"]
    chunk_index: int                  # 0-based index within the article
    total_chunks_in_article: int      # Total chunks this article produced
    text: str                         # The chunk text content
    word_count: int
    estimated_tokens: int
    has_code: bool
    has_list: bool
    has_image_refs: bool
    chunk_type: str                   # "structural_h2", "structural_h3", "fixed_window", "single"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ArticleContent:
    """Parsed article content ready for chunking."""
    url: str
    title: str
    section: str
    html: str                         # Raw HTML of the article body
    sections: list[HeadingSection] = field(default_factory=list)


@dataclass
class HeadingSection:
    """A section of content under a heading."""
    level: int                        # 1-6 for h1-h6
    heading_text: str
    content_html: str                 # HTML content under this heading
    content_text: str                 # Plain text content
    subsections: list[HeadingSection] = field(default_factory=list)


# ---------------------------------------------------------------------------
# HTML content extraction
# ---------------------------------------------------------------------------
STRIP_TAGS = {"nav", "footer", "header", "aside", "script", "style", "noscript"}
STRIP_CLASSES = {
    "sidebar", "navigation", "nav", "footer", "header", "menu",
    "breadcrumb", "widget", "comment", "social", "share", "cookie",
    "popup", "modal", "banner",
}


def extract_article_body(html: str) -> Tag:
    """Extract the main article content, stripping nav/footer/sidebar."""
    soup = BeautifulSoup(html, "lxml")

    # Find main content container
    main = (
        soup.find("article")
        or soup.find("main")
        or soup.find("div", class_=re.compile(r"(entry.content|article.content|guide.content|kb.content|post.content)", re.I))
        or soup.find("div", class_=re.compile(r"(content|article|guide|kb)", re.I))
        or soup.find("div", id=re.compile(r"(content|article|guide|main)", re.I))
    )
    if main is None:
        main = soup.find("body") or soup

    # Remove unwanted elements
    for tag_name in STRIP_TAGS:
        for el in main.find_all(tag_name):
            el.decompose()
    for el in main.find_all(True, class_=True):
        classes = " ".join(el.get("class", []))
        if any(c in classes.lower() for c in STRIP_CLASSES):
            el.decompose()
    for comment in main.find_all(string=lambda t: isinstance(t, Comment)):
        comment.extract()

    return main


def get_clean_text(element) -> str:
    """Get clean text from a BeautifulSoup element, preserving meaningful whitespace."""
    if element is None:
        return ""
    text = element.get_text(separator=" ", strip=True)
    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


def get_structured_text(element) -> str:
    """
    Get text from a BeautifulSoup element, preserving structure:
    - Newlines between block elements
    - Bullet/number markers for list items
    - Code block formatting
    """
    if element is None:
        return ""

    parts = []
    for child in element.children:
        if isinstance(child, NavigableString):
            text = str(child).strip()
            if text:
                parts.append(text)
        elif isinstance(child, Tag):
            tag = child.name.lower()

            if tag in HEADING_TAGS:
                # Don't include heading text in section body — it's in the breadcrumb
                continue
            elif tag in ("p", "div", "section", "blockquote"):
                text = get_structured_text(child)
                if text:
                    parts.append(f"\n{text}\n")
            elif tag == "pre":
                code_text = child.get_text()
                parts.append(f"\n```\n{code_text}\n```\n")
            elif tag == "code" and child.parent and child.parent.name != "pre":
                parts.append(f"`{child.get_text()}`")
            elif tag == "ul":
                for li in child.find_all("li", recursive=False):
                    li_text = get_structured_text(li)
                    if li_text:
                        parts.append(f"\n- {li_text}")
                parts.append("\n")
            elif tag == "ol":
                for i, li in enumerate(child.find_all("li", recursive=False), 1):
                    li_text = get_structured_text(li)
                    if li_text:
                        parts.append(f"\n{i}. {li_text}")
                parts.append("\n")
            elif tag == "li":
                text = get_structured_text(child)
                if text:
                    parts.append(text)
            elif tag == "br":
                parts.append("\n")
            elif tag == "img":
                alt = child.get("alt", "").strip()
                if alt:
                    parts.append(f"[Image: {alt}]")
            elif tag == "table":
                parts.append(_table_to_text(child))
            elif tag == "a":
                text = child.get_text(strip=True)
                href = child.get("href", "")
                if text:
                    parts.append(text)
            else:
                text = get_structured_text(child)
                if text:
                    parts.append(text)

    result = " ".join(parts)
    result = re.sub(r" +", " ", result)
    result = re.sub(r"\n ", "\n", result)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


def _table_to_text(table_tag: Tag) -> str:
    """Convert an HTML table to a simple text representation."""
    rows = []
    for tr in table_tag.find_all("tr"):
        cells = []
        for td in tr.find_all(["td", "th"]):
            cells.append(td.get_text(strip=True))
        if cells:
            rows.append(" | ".join(cells))
    if rows:
        return "\n" + "\n".join(rows) + "\n"
    return ""


# ---------------------------------------------------------------------------
# Heading-based section parser
# ---------------------------------------------------------------------------

def parse_sections(body: Tag) -> list[HeadingSection]:
    """
    Parse a body element into a tree of HeadingSection objects.
    This walks through the direct children and splits content by heading tags.
    """
    sections: list[HeadingSection] = []
    current_heading: Optional[str] = None
    current_level: int = 0
    current_elements: list = []

    # Flatten nested divs to find headings at any depth
    all_elements = _linearize_content(body)

    for el in all_elements:
        if isinstance(el, Tag) and el.name in HEADING_TAGS:
            # Save previous section
            if current_elements or current_heading:
                section = _build_section(current_level, current_heading or "", current_elements)
                if section:
                    sections.append(section)

            current_heading = el.get_text(strip=True)
            current_level = int(el.name[1])
            current_elements = []
        else:
            current_elements.append(el)

    # Save final section
    if current_elements or current_heading:
        section = _build_section(current_level, current_heading or "", current_elements)
        if section:
            sections.append(section)

    # Nest H3 sections under their parent H2
    sections = _nest_sections(sections)

    return sections


def _linearize_content(element: Tag) -> list:
    """
    Walk through the element tree and produce a flat list of elements,
    where headings are kept as markers and content blocks are preserved.
    This handles the common case where headings and content are wrapped
    in various div containers.
    """
    result = []
    for child in element.children:
        if isinstance(child, NavigableString):
            text = str(child).strip()
            if text:
                result.append(child)
        elif isinstance(child, Tag):
            if child.name in HEADING_TAGS:
                result.append(child)
            elif child.name in ("div", "section", "article"):
                # Check if this div contains headings — if so, recurse
                has_headings = child.find(HEADING_TAGS)
                if has_headings:
                    result.extend(_linearize_content(child))
                else:
                    result.append(child)
            else:
                result.append(child)
    return result


def _build_section(level: int, heading: str, elements: list) -> Optional[HeadingSection]:
    """Build a HeadingSection from collected elements."""
    # Create a temporary container to get structured text
    from bs4 import BeautifulSoup as BS
    container = BS("<div></div>", "lxml").find("div")
    for el in elements:
        if isinstance(el, (Tag, NavigableString)):
            container.append(el.__copy__() if hasattr(el, '__copy__') else el)

    content_text = get_structured_text(container)
    content_html = str(container)

    if not content_text.strip() and not heading:
        return None

    return HeadingSection(
        level=level,
        heading_text=heading,
        content_html=content_html,
        content_text=content_text,
    )


def _nest_sections(sections: list[HeadingSection]) -> list[HeadingSection]:
    """Nest H3 sections under the preceding H2, H4 under H3, etc."""
    if not sections:
        return sections

    result: list[HeadingSection] = []
    stack: list[HeadingSection] = []

    for section in sections:
        # Pop stack until we find a parent with lower heading level
        while stack and stack[-1].level >= section.level:
            stack.pop()

        if stack:
            stack[-1].subsections.append(section)
        else:
            result.append(section)

        stack.append(section)

    return result


# ---------------------------------------------------------------------------
# Tokenization helpers
# ---------------------------------------------------------------------------

def estimate_tokens(text: str) -> int:
    """Estimate token count from text."""
    words = text.split()
    return int(len(words) * TOKENS_PER_WORD)


def word_count(text: str) -> int:
    return len(text.split())


# ---------------------------------------------------------------------------
# Core chunking logic
# ---------------------------------------------------------------------------

def chunk_article(
    url: str,
    title: str,
    section_category: str,
    html: str,
) -> list[Chunk]:
    """
    Chunk a single article using the hybrid structural/fixed-token strategy.

    Args:
        url: Article URL
        title: Article title
        section_category: Category/section name
        html: Raw HTML of the article page

    Returns:
        List of Chunk objects
    """
    body = extract_article_body(html)
    sections = parse_sections(body)

    raw_chunks: list[tuple[str, list[str], str]] = []  # (text, breadcrumb, chunk_type)

    if not sections:
        # No structure found — treat full body as flat text
        full_text = get_structured_text(body)
        raw_chunks.extend(_chunk_flat_text(full_text, [title], "single"))
    else:
        # Check if we have H2-level sections or only H1/intro
        has_h2 = any(s.level == 2 for s in sections)

        if not has_h2:
            # All content is under H1 or no headings — treat as flat
            full_text = "\n\n".join(
                (f"{s.heading_text}\n{s.content_text}" if s.heading_text else s.content_text)
                for s in sections
            )
            raw_chunks.extend(_chunk_flat_text(full_text, [title], "single"))
        else:
            # Process H2-level sections
            # First, collect any intro content before the first H2
            for section in sections:
                if section.level < 2 or section.level == 0:
                    # Intro content
                    if section.content_text.strip():
                        intro_text = section.content_text
                        raw_chunks.extend(
                            _chunk_flat_text(intro_text, [title, "(Introduction)"], "structural_h2")
                        )
                elif section.level == 2:
                    _chunk_h2_section(section, [title], raw_chunks)

    # Build final Chunk objects with IDs and metadata
    chunks: list[Chunk] = []
    for i, (text, breadcrumb, chunk_type) in enumerate(raw_chunks):
        wc = word_count(text)
        if wc < MIN_CHUNK_WORDS:
            continue

        chunk_id = _make_chunk_id(url, i, text)

        chunks.append(Chunk(
            chunk_id=chunk_id,
            article_url=url,
            article_title=title,
            section_category=section_category,
            heading_breadcrumb=breadcrumb,
            chunk_index=i,
            total_chunks_in_article=0,  # Will be set below
            text=text,
            word_count=wc,
            estimated_tokens=estimate_tokens(text),
            has_code=bool(re.search(r"```", text)),
            has_list=bool(re.search(r"^\s*[-\d]+[\.\)]\s", text, re.MULTILINE)),
            has_image_refs=bool(re.search(r"\[Image:", text)),
            chunk_type=chunk_type,
        ))

    # Set total_chunks_in_article and re-index
    for i, chunk in enumerate(chunks):
        chunk.chunk_index = i
        chunk.total_chunks_in_article = len(chunks)

    return chunks


def _chunk_h2_section(
    section: HeadingSection,
    parent_breadcrumb: list[str],
    raw_chunks: list[tuple[str, list[str], str]],
):
    """Process an H2-level section, potentially sub-splitting on H3."""
    breadcrumb = parent_breadcrumb + [section.heading_text]
    section_text = section.content_text
    tokens = estimate_tokens(section_text)

    if tokens <= MAX_CHUNK_TOKENS:
        # Section fits in one chunk — include heading as context
        chunk_text = f"{section.heading_text}\n\n{section_text}" if section.heading_text else section_text
        raw_chunks.append((chunk_text.strip(), breadcrumb, "structural_h2"))
    elif section.subsections:
        # Section too large but has H3 subsections — split on H3
        # First, any content before the first H3
        if section.content_text.strip():
            # Content directly under H2, before any H3
            direct_text = _get_direct_content(section)
            if direct_text.strip():
                header = f"{section.heading_text}\n\n" if section.heading_text else ""
                raw_chunks.extend(
                    _chunk_flat_text(f"{header}{direct_text}", breadcrumb, "structural_h2")
                )

        for subsection in section.subsections:
            sub_breadcrumb = breadcrumb + [subsection.heading_text]
            sub_text = f"{subsection.heading_text}\n\n{subsection.content_text}" if subsection.heading_text else subsection.content_text
            sub_tokens = estimate_tokens(sub_text)

            if sub_tokens <= MAX_CHUNK_TOKENS:
                raw_chunks.append((sub_text.strip(), sub_breadcrumb, "structural_h3"))
            else:
                # H3 section still too large — fixed-token window
                raw_chunks.extend(
                    _chunk_flat_text(sub_text, sub_breadcrumb, "fixed_window")
                )
    else:
        # Section too large but no H3 subsections — fixed-token window
        header = f"{section.heading_text}\n\n" if section.heading_text else ""
        raw_chunks.extend(
            _chunk_flat_text(f"{header}{section_text}", breadcrumb, "fixed_window")
        )


def _get_direct_content(section: HeadingSection) -> str:
    """Get content directly under a section, excluding subsection content."""
    if not section.subsections:
        return section.content_text

    # Remove subsection text from the section text
    # This is approximate — we take text before the first subsection heading
    full_text = section.content_text
    first_sub_heading = section.subsections[0].heading_text
    if first_sub_heading and first_sub_heading in full_text:
        idx = full_text.index(first_sub_heading)
        return full_text[:idx].strip()
    return ""


def _chunk_flat_text(
    text: str,
    breadcrumb: list[str],
    chunk_type: str,
) -> list[tuple[str, list[str], str]]:
    """
    Chunk flat text using fixed-token windowing with overlap.
    If the text fits in one chunk, returns it as-is.
    """
    tokens = estimate_tokens(text)

    if tokens <= MAX_CHUNK_TOKENS:
        return [(text.strip(), breadcrumb, chunk_type)]

    # Fixed-token windowing
    words = text.split()
    max_words = int(MAX_CHUNK_TOKENS / TOKENS_PER_WORD)
    overlap_words = int(OVERLAP_TOKENS / TOKENS_PER_WORD)
    step = max_words - overlap_words

    chunks = []
    start = 0
    window_idx = 0
    while start < len(words):
        end = min(start + max_words, len(words))
        chunk_words = words[start:end]
        chunk_text = " ".join(chunk_words)

        # Try to break at sentence boundary
        if end < len(words):
            chunk_text = _break_at_sentence(chunk_text, words[end:])

        window_breadcrumb = breadcrumb + [f"(part {window_idx + 1})"]
        actual_type = "fixed_window" if chunk_type != "single" else chunk_type
        chunks.append((chunk_text.strip(), window_breadcrumb, actual_type))

        start += step
        window_idx += 1

        # Safety: avoid infinite loop
        if window_idx > 100:
            break

    return chunks


def _break_at_sentence(text: str, remaining_words: list[str]) -> str:
    """
    Try to break text at the last sentence boundary (.!?) to avoid
    cutting mid-sentence. Only looks at the last ~20% of the text.
    """
    # Find last sentence-ending punctuation in the last 20% of text
    cutoff = int(len(text) * 0.8)
    last_part = text[cutoff:]

    for pattern in [". ", ".\n", "! ", "? ", ":\n"]:
        idx = last_part.rfind(pattern)
        if idx >= 0:
            return text[:cutoff + idx + 1]

    return text


def _make_chunk_id(url: str, index: int, text: str) -> str:
    """Create a deterministic chunk ID from URL, index, and content hash."""
    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()[:8]
    return f"halo_{url_hash}_{index:03d}_{content_hash}"


# ---------------------------------------------------------------------------
# Convenience: chunk from plain text (no HTML)
# ---------------------------------------------------------------------------

def chunk_plain_text(
    url: str,
    title: str,
    section_category: str,
    text: str,
    headings: dict[str, list[str]] | None = None,
) -> list[Chunk]:
    """
    Chunk plain text content (when HTML is not available).
    Uses heading metadata from the manifest to simulate structure.

    Args:
        url: Article URL
        title: Article title
        section_category: Category/section name
        text: Plain text content of the article
        headings: Optional dict of heading lists like {"h2": ["Section 1", "Section 2"]}

    Returns:
        List of Chunk objects
    """
    if headings and headings.get("h2"):
        # Simulate structural chunking using heading names as section markers
        h2_headings = headings["h2"]
        sections = _split_text_by_headings(text, h2_headings)

        raw_chunks = []
        for heading, section_text in sections:
            breadcrumb = [title]
            if heading:
                breadcrumb.append(heading)

            tokens = estimate_tokens(section_text)
            if tokens <= MAX_CHUNK_TOKENS:
                full_text = f"{heading}\n\n{section_text}" if heading else section_text
                raw_chunks.append((full_text.strip(), breadcrumb, "structural_h2"))
            else:
                header = f"{heading}\n\n" if heading else ""
                raw_chunks.extend(
                    _chunk_flat_text(f"{header}{section_text}", breadcrumb, "fixed_window")
                )
    else:
        # Flat content — use fixed-token windowing
        raw_chunks = _chunk_flat_text(text, [title], "single")

    # Build final chunks
    chunks = []
    for i, (chunk_text, breadcrumb, chunk_type) in enumerate(raw_chunks):
        wc = word_count(chunk_text)
        if wc < MIN_CHUNK_WORDS:
            continue

        chunk_id = _make_chunk_id(url, i, chunk_text)
        chunks.append(Chunk(
            chunk_id=chunk_id,
            article_url=url,
            article_title=title,
            section_category=section_category,
            heading_breadcrumb=breadcrumb,
            chunk_index=i,
            total_chunks_in_article=0,
            text=chunk_text,
            word_count=wc,
            estimated_tokens=estimate_tokens(chunk_text),
            has_code=bool(re.search(r"```|`[^`]+`", chunk_text)),
            has_list=bool(re.search(r"^\s*[-\d]+[\.\)]\s", chunk_text, re.MULTILINE)),
            has_image_refs=bool(re.search(r"\[Image:", chunk_text)),
            chunk_type=chunk_type,
        ))

    for i, chunk in enumerate(chunks):
        chunk.chunk_index = i
        chunk.total_chunks_in_article = len(chunks)

    return chunks


def _split_text_by_headings(text: str, headings: list[str]) -> list[tuple[str, str]]:
    """
    Split text by heading markers. Returns list of (heading, content) tuples.
    The first tuple may have an empty heading (intro content).
    """
    # Build regex pattern to split on any heading line
    sections = []
    remaining = text
    last_heading = ""

    for heading in headings:
        # Look for the heading in the remaining text
        escaped = re.escape(heading)
        match = re.search(rf"(?:^|\n)\s*{escaped}\s*(?:\n|$)", remaining, re.IGNORECASE)
        if match:
            # Content before this heading
            before = remaining[:match.start()].strip()
            if before or last_heading:
                sections.append((last_heading, before))

            last_heading = heading
            remaining = remaining[match.end():].strip()
        # If heading not found, just continue

    # Final section
    if remaining or last_heading:
        sections.append((last_heading, remaining))

    if not sections:
        sections = [("", text)]

    return sections
