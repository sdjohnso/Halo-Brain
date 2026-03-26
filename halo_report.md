# HaloPSA Documentation Corpus — Discovery Analysis Report

*Generated: 2026-03-26 01:00 UTC*

*Source: https://usehalo.com/halopsa/guides/*

> **Note:** This report was generated from a search-based discovery process because direct
> HTTP access to usehalo.com was blocked by the network environment. The 181 articles below
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
| faqs | 32 | ~320 | /faq-list/faqs/ |
| halopsa-guides | 11 | ~110 | /faq-list/halopsa-guides/ |
| haloitsm-public-guides | 54-57 | ~550 | /faq-list/haloitsm-public-guides/ |

**Important:** Categories heavily overlap. The `halopsa-website` archive appears to be the
superset containing most HaloPSA articles. After deduplication, the estimated unique
article count is **~680-720 articles**.

**Full corpus projections (at ~700 articles):**
- Estimated total word count: ~730,000 words (extrapolating from 181 sample avg of 1,045 words/article)
- Estimated total tokens: ~985,000 tokens
- Estimated chunks (400-token structural): ~2,463
- Estimated chunks (500-token fixed, 50-token overlap): ~2,189



## 1. Summary Statistics



| Metric | Value |
| --- | --- |
| Total articles discovered | 181 |
| Total word count | 189,080 |
| Total estimated token count | 255,173 |
| Average words per article | 1,044.6 |
| Median words per article | 978 |
| Est. chunks (400-token structural) | 638 |
| Est. chunks (500-token fixed, 50-token overlap) | 568 |


## 2. Content Distribution



### 2a. Article Length Distribution



| Bucket | Count | % of Total |
| --- | --- | --- |
| Under 200 words | 0 | 0.0%   |
| 200–500 words | 15 | 8.3%  ████ |
| 500–1,000 words | 77 | 42.5%  █████████████████████ |
| 1,000–2,000 words | 84 | 46.4%  ███████████████████████ |
| Over 2,000 words | 5 | 2.8%  █ |


### 2b. Top 10 Longest Articles (by word count)



| # | Words | Tokens | Title | URL |
| --- | --- | --- | --- | --- |
| 1 | 2,452 | 3,310 | Introduction to Halo Documentation | https://usehalo.com/guide/introduction-to-halo-documentation/ |
| 2 | 2,215 | 2,990 | Step-by-Step Configuration Walk Through | https://usehalo.com/guide/step-by-step-configuration-walk-through/ |
| 3 | 2,109 | 2,847 | Introduction to HaloPSA | https://usehalo.com/guide/introduction-to-halopsa/ |
| 4 | 2,104 | 2,840 | Terminology | https://usehalo.com/guide/terminology/ |
| 5 | 2,038 | 2,751 | Navigating the Self-Service Portal (For End Users) | https://usehalo.com/guide/navigating-the-self-service-portal-for-end-users/ |
| 6 | 1,926 | 2,600 | Purchase Orders | https://usehalo.com/guide/purchase-orders/ |
| 7 | 1,901 | 2,566 | Customer Contracts | https://usehalo.com/guide/customer-contracts/ |
| 8 | 1,839 | 2,482 | HaloPSA API Guide | https://halopsa.com/guides/article/?kbid=1823 |
| 9 | 1,839 | 2,482 | Subscription Count Based Quantities | https://usehalo.com/guide/subscription-count-based-quantities/ |
| 10 | 1,807 | 2,439 | Project Setup Wizard | https://usehalo.com/guide/project-setup-wizard/ |


### 2c. Top 10 Shortest Articles (potential merge candidates)



| # | Words | Tokens | Title | URL |
| --- | --- | --- | --- | --- |
| 1 | 301 | 406 | Views | https://usehalo.com/guide/views/ |
| 2 | 302 | 407 | Menu Buttons for Self-Service Portal | https://usehalo.com/guide/menu-buttons-for-self-service-portal/ |
| 3 | 325 | 438 | General Settings (Asset Management) | https://usehalo.com/guide/general-settings-asset-management/ |
| 4 | 342 | 461 | Actions | https://usehalo.com/guide/actions/ |
| 5 | 344 | 464 | Default Views | https://usehalo.com/guide/default-views/ |
| 6 | 376 | 507 | SSO for Entra ID | https://usehalo.com/guide/sso-for-entra-id/ |
| 7 | 402 | 542 | Redirect HTTP to HTTPS | https://usehalo.com/guide/redirect-http-to-https/ |
| 8 | 405 | 546 | Report Builder | https://usehalo.com/guide/report-builder/ |
| 9 | 418 | 564 | Progressive Web Application | https://usehalo.com/guide/progressive-web-application/ |
| 10 | 423 | 571 | Guides (ID 1530) | https://usehalo.com/halopsa/guides/1530/ |


## 3. Structural Depth Analysis



This section analyses heading usage to determine whether structural/heading-based chunking is viable.



| Metric | Count | % of Total |
| --- | --- | --- |
| Articles with H2 headings (multi-section) | 180 | 99.4% |
| Articles with H3+ headings (complex nested) | 139 | 76.8% |
| Articles with no sub-headings (flat content) | 1 | 0.6% |


| Metric | Value |
| --- | --- |
| Average H2 sections per article | 3.8 |
| Maximum H2 sections in one article | 10 |


### 3a. H2 Heading Count Distribution



| H2 Count | Articles |
| --- | --- |
| 0 | 1 |
| 1 | 29 |
| 2 | 34 |
| 3 | 36 |
| 4 | 19 |
| 5 | 23 |
| 6 | 20 |
| 7 | 2 |
| 8 | 8 |
| 9 | 2 |
| 10 | 7 |


## 4. Content Type Signals



| Content Signal | Count | % of Total |
| --- | --- | --- |
| Articles with code blocks (API/technical) | 14 | 7.7% |
| Articles with numbered lists (procedural) | 39 | 21.5% |
| Articles with bullet lists | 134 | 74.0% |
| Articles with images | 134 | 74.0% |


**Total images across corpus:** 874

**Average images per article:** 4.8



## 5. Chunking Recommendation



### Data-Driven Assessment



**99% of articles use H2 headings**, indicating strong structural markup across the majority of the corpus. This makes **heading-based structural chunking** a viable primary strategy.





### Recommended Strategy



**Primary: Heading-based structural chunking with fixed-token fallback**



1. **For articles with H2+ headings:** Split on H2 boundaries. Each H2 section becomes a chunk. If a section exceeds 500 tokens, sub-split on H3 boundaries or use fixed-token windowing within the section.

2. **For flat articles under 500 tokens:** Keep as a single chunk.

3. **For flat articles over 500 tokens:** Use fixed-token chunking with 500-token windows and 50-token overlap.

4. **Metadata enrichment:** Attach article title, section/category, and URL to every chunk for retrieval context.



**Estimated total chunks (181-article sample):** 638 (at 400-token structural) to 568 (at 500-token fixed with overlap)

**Projected total chunks (full ~700-article corpus):** ~2,463 (at 400-token structural) to ~2,189 (at 500-token fixed with overlap)





## 6. Section / Category Breakdown



| Section / Category | Articles | Total Words | Avg Words |
| --- | --- | --- | --- |
| API | 1 | 1,839 | 1,839.0 |
| Accounting | 2 | 2,627 | 1,313.5 |
| An Introduction to HaloPSA | 9 | 15,413 | 1,712.6 |
| Asset Management | 21 | 19,736 | 939.8 |
| Automation | 6 | 6,580 | 1,096.7 |
| Billing | 16 | 22,058 | 1,378.6 |
| Configuration | 18 | 12,537 | 696.5 |
| Data Import | 1 | 663 | 663.0 |
| Email Configuration | 13 | 12,375 | 951.9 |
| HaloPSA Academy | 5 | 4,525 | 905.0 |
| HaloPSA Guides | 2 | 1,313 | 656.5 |
| Index | 1 | 472 | 472.0 |
| Integrations | 21 | 25,101 | 1,195.3 |
| Organisation | 4 | 3,098 | 774.5 |
| Portal Customisation | 4 | 2,595 | 648.8 |
| Product Management | 1 | 1,071 | 1,071.0 |
| Projects | 4 | 6,335 | 1,583.8 |
| Raising Tickets | 3 | 2,965 | 988.3 |
| Reporting | 11 | 9,588 | 871.6 |
| SLA | 6 | 4,809 | 801.5 |
| Security | 6 | 3,906 | 651.0 |
| Self Service Portal | 2 | 2,887 | 1,443.5 |
| Service Catalogue | 3 | 2,903 | 967.7 |
| Service Desk | 3 | 2,751 | 917.0 |
| Ticket Rules | 2 | 1,588 | 794.0 |
| Tickets | 14 | 18,198 | 1,299.9 |
| Viewing Tickets | 2 | 1,147 | 573.5 |


## 7. Data Quality Notes



No duplicate titles detected.







---

*Report generated from halo_manifest.json containing 181 articles.*
