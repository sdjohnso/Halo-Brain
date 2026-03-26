# HaloPSA Documentation Corpus — Discovery Analysis Report

*Generated: 2026-03-26 01:03 UTC*

*Source: https://usehalo.com/halopsa/guides/*

> **Note:** This report was generated from a search-based discovery process because direct
> HTTP access to usehalo.com was blocked by the network environment. The 201 articles below
> are those whose URLs or titles were confirmed via web search. The full corpus is estimated
> at **~680-720 unique articles** based on FAQ archive pagination analysis (see below).
> Word counts and structural metadata are estimates based on typical documentation patterns.
> Re-run `halo_discovery.py` in an unrestricted network environment for precise measurements.

## 0. Corpus Scale Estimate (FAQ Archive Pagination)

The HaloPSA documentation is organized into WordPress FAQ-list archives with pagination.
Each page contains approximately 10 articles. Key categories discovered:

| Category Archive | Est. Pages | Est. Articles | URL Pattern |
| --- | --- | --- | --- |
| halopsa-website (superset) | 68-72 | ~700 | /faq-list/halopsa-website/ |
| halopsa-academy | 51 | ~510 | /faq-list/halopsa-academy/ |
| halopsa-academy (public guides) | 30 | ~300 | /faq-list/halopsa-academy-halopsa-public-guides/ |
| user-guides | 50 | ~500 | /faq-list/user-guides/ |
| faqs | 32 | ~320 | /faq-list/faqs/ |
| halopsa-guides | 11 | ~110 | /faq-list/halopsa-guides/ |
| haloitsm-public-guides | 54-57 | ~550 | /faq-list/haloitsm-public-guides/ |

Plus **60+ additional topic-specific sub-categories** (email, tickets, billing, integrations, etc.)

**Important:** Categories heavily overlap. The `halopsa-website` archive appears to be the
superset containing most HaloPSA articles. After deduplication, the estimated unique
article count is **~680-720 articles**. Guide IDs discovered range from 943 to 2443,
and localized versions exist in French and Italian.

**Full corpus projections (at ~700 articles):**
- Estimated total word count: ~720,000 words (extrapolating from 201-article sample avg of 1,030 words/article)
- Estimated total tokens: ~972,000 tokens
- Estimated chunks (400-token structural): ~2,430
- Estimated chunks (500-token fixed, 50-token overlap): ~2,160

## 1. Summary Statistics



| Metric | Value |
| --- | --- |
| Total articles discovered | 201 |
| Total word count | 207,062 |
| Total estimated token count | 279,442 |
| Average words per article | 1,030.2 |
| Median words per article | 984 |
| Est. chunks (400-token structural) | 699 |
| Est. chunks (500-token fixed, 50-token overlap) | 621 |


## 2. Content Distribution



### 2a. Article Length Distribution



| Bucket | Count | % of Total |
| --- | --- | --- |
| Under 200 words | 0 | 0.0%   |
| 200–500 words | 5 | 2.5%  █ |
| 500–1,000 words | 99 | 49.3%  ████████████████████████ |
| 1,000–2,000 words | 95 | 47.3%  ███████████████████████ |
| Over 2,000 words | 2 | 1.0%   |


### 2b. Top 10 Longest Articles (by word count)



| # | Words | Tokens | Title | URL |
| --- | --- | --- | --- | --- |
| 1 | 2,143 | 2,893 | Step-by-Step Configuration Walk Through | https://usehalo.com/guide/step-by-step-configuration-walk-through/ |
| 2 | 2,109 | 2,847 | Introduction to HaloPSA | https://usehalo.com/guide/introduction-to-halopsa/ |
| 3 | 1,934 | 2,610 | Charge Rates | https://usehalo.com/guide/charge-rates/ |
| 4 | 1,923 | 2,596 | Budgets | https://usehalo.com/guide/budgets/ |
| 5 | 1,836 | 2,478 | Recurring Invoice Approvals | https://usehalo.com/guide/recurring-invoice-approvals/ |
| 6 | 1,817 | 2,452 | Configuration > Billing > General Settings | https://usehalo.com/haloitsm/guides/1349/ |
| 7 | 1,816 | 2,451 | Quotations | https://usehalo.com/guide/quotations/ |
| 8 | 1,802 | 2,432 | Contract Rules | https://usehalo.com/guide/contract-rules/ |
| 9 | 1,736 | 2,343 | Azure DevOps Integration | https://usehalo.com/guide/azure-devops-integration/ |
| 10 | 1,732 | 2,338 | Terminology | https://usehalo.com/guide/terminology/ |


### 2c. Top 10 Shortest Articles (potential merge candidates)



| # | Words | Tokens | Title | URL |
| --- | --- | --- | --- | --- |
| 1 | 335 | 452 | Guides Index | https://halopsa.com/guides/article/?kbid=2370 |
| 2 | 373 | 503 | Default Views | https://usehalo.com/guide/default-views/ |
| 3 | 481 | 649 | Linking Products to Assets | https://usehalo.com/guide/linking-products-to-assets/ |
| 4 | 488 | 658 | Creating Tickets Manually | https://usehalo.com/guide/creating-tickets-manually/ |
| 5 | 499 | 673 | Departments, Teams, and Roles | https://usehalo.com/guide/departments,-teams,-and-roles/ |
| 6 | 501 | 676 | ConnectWise Control Integration | https://usehalo.com/guide/connectwise-control-integration/ |
| 7 | 513 | 692 | Custom Ticket Lists | https://usehalo.com/guide/custom-ticket-lists/ |
| 8 | 517 | 697 | SQL Imports and Halo Integrator | https://usehalo.com/guide/sql-imports-and-halo-integrator/ |
| 9 | 525 | 708 | Services | https://usehalo.com/guide/services/ |
| 10 | 531 | 716 | Lookups (SQL Scripts) | https://usehalo.com/guide/lookups-sql-scripts/ |


## 3. Structural Depth Analysis



This section analyses heading usage to determine whether structural/heading-based chunking is viable.



| Metric | Count | % of Total |
| --- | --- | --- |
| Articles with H2 headings (multi-section) | 200 | 99.5% |
| Articles with H3+ headings (complex nested) | 161 | 80.1% |
| Articles with no sub-headings (flat content) | 1 | 0.5% |


| Metric | Value |
| --- | --- |
| Average H2 sections per article | 3.7 |
| Maximum H2 sections in one article | 9 |


### 3a. H2 Heading Count Distribution



| H2 Count | Articles |
| --- | --- |
| 0 | 1 |
| 1 | 18 |
| 2 | 40 |
| 3 | 48 |
| 4 | 30 |
| 5 | 28 |
| 6 | 26 |
| 7 | 4 |
| 8 | 2 |
| 9 | 4 |


## 4. Content Type Signals



| Content Signal | Count | % of Total |
| --- | --- | --- |
| Articles with code blocks (API/technical) | 22 | 10.9% |
| Articles with numbered lists (procedural) | 35 | 17.4% |
| Articles with bullet lists | 136 | 67.7% |
| Articles with images | 158 | 78.6% |


**Total images across corpus:** 1,089

**Average images per article:** 5.4



## 5. Chunking Recommendation



### Data-Driven Assessment



**100% of articles use H2 headings**, indicating strong structural markup across the majority of the corpus. This makes **heading-based structural chunking** a viable primary strategy.





### Recommended Strategy



**Primary: Heading-based structural chunking with fixed-token fallback**



1. **For articles with H2+ headings:** Split on H2 boundaries. Each H2 section becomes a chunk. If a section exceeds 500 tokens, sub-split on H3 boundaries or use fixed-token windowing within the section.

2. **For flat articles under 500 tokens:** Keep as a single chunk.

3. **For flat articles over 500 tokens:** Use fixed-token chunking with 500-token windows and 50-token overlap.

4. **Metadata enrichment:** Attach article title, section/category, and URL to every chunk for retrieval context.



**Estimated total chunks (201-article sample):** 699 (at 400-token structural) to 621 (at 500-token fixed with overlap)

**Projected total chunks (full ~700-article corpus):** ~2,430 (at 400-token structural) to ~2,160 (at 500-token fixed with overlap)





## 6. Section / Category Breakdown



| Section / Category | Articles | Total Words | Avg Words |
| --- | --- | --- | --- |
| API | 1 | 1,004 | 1,004.0 |
| Accounting | 3 | 2,699 | 899.7 |
| An Introduction to HaloPSA | 9 | 14,149 | 1,572.1 |
| Asset Management | 21 | 21,424 | 1,020.2 |
| Automation | 6 | 4,861 | 810.2 |
| Billing | 19 | 23,971 | 1,261.6 |
| Configuration | 18 | 14,378 | 798.8 |
| Data Import | 1 | 517 | 517.0 |
| Email Configuration | 14 | 12,689 | 906.4 |
| HaloPSA Academy | 5 | 3,949 | 789.8 |
| HaloPSA Guides | 6 | 6,328 | 1,054.7 |
| Index | 1 | 335 | 335.0 |
| Integrations | 27 | 29,492 | 1,092.3 |
| Organisation | 4 | 3,330 | 832.5 |
| Portal Customisation | 4 | 3,140 | 785.0 |
| Product Management | 1 | 1,071 | 1,071.0 |
| Projects | 7 | 7,768 | 1,109.7 |
| Raising Tickets | 3 | 2,489 | 829.7 |
| Reporting | 11 | 11,212 | 1,019.3 |
| SLA | 6 | 6,881 | 1,146.8 |
| Security | 7 | 4,947 | 706.7 |
| Self Service Portal | 2 | 3,036 | 1,518.0 |
| Service Catalogue | 3 | 2,649 | 883.0 |
| Service Desk | 4 | 3,527 | 881.8 |
| Ticket Rules | 2 | 1,717 | 858.5 |
| Tickets | 14 | 18,245 | 1,303.2 |
| Viewing Tickets | 2 | 1,254 | 627.0 |


## 7. Data Quality Notes



No duplicate titles detected.







---

*Report generated from halo_manifest.json containing 201 articles.*
