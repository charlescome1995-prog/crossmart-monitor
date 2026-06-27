# Dev.to Content Matrix for CrossMart

Goal: turn the CrossMart build process into a Dev.to content series that attracts developers, indie hackers, and Amazon/e-commerce operators without sounding like hard advertising.

Working principle: each article should teach one practical thing, then softly point readers to the relevant CrossMart page.

## Current inventory

- Full draft found: `01-amazon-competitor-monitor-python-edge-github-pages.md`
- Existing plan found: 6-article sequence in `README.md`
- Cleaned plan below: expanded to 9 publishable angles, with overlap removed by assigning each article a unique job.

## Duplicate cleanup logic

| Overlap risk | Cleanup decision |
|---|---|
| Monitor build story vs Edge CDP technical story | Article 01 stays as the product/build story; Article 06 becomes a narrower technical deep dive on real-browser automation. |
| Snapshot-first data vs backendless GitHub Pages architecture | Article 05 focuses on data modeling and debugging; Article 07 focuses on deployment architecture and cost. |
| Selector, Listing, Ops all use competitor data | Each gets a different user question: what to sell, how to write the listing, what competitors are doing operationally. |
| Full CrossMart suite recap vs individual tool posts | Article 09 becomes the end-of-series narrative and internal-tool productization lesson, not another feature list. |

## Final 9-article sequence

| # | Working title | Primary audience | Core angle | Primary CTA | Status |
|---|---|---|---|---|---|
| 01 | I Built an Amazon Competitor Monitor with Python, Edge CDP, and GitHub Pages | Developers + e-commerce operators | Build-in-public case study for CrossMart Monitor | CrossMart Monitor | Full draft ready for review |
| 02 | Turning Seller Tool Keyword Exports into a Product Opportunity Engine | Amazon operators + indie hackers | How keyword spreadsheets become ranked product opportunities | CrossMart Selector | Outline needed |
| 03 | Building an AI Amazon Listing Builder from Competitor ASINs | Operators + AI builders | Extract competitor patterns, then generate structured listing drafts | CrossMart Listing Builder | Outline needed |
| 04 | From Traffic Keywords to Competitor Operations Diagnosis | Amazon operators | Traffic source, ad-insight, and review analysis as an operations dashboard | CrossMart Ops | Outline needed |
| 05 | Why Snapshot-First Data Beats One-Off Scraping for Market Monitoring | Developers | Data architecture: snapshots, diffs, debugging, change detection | CrossMart Monitor + suite links | Outline needed |
| 06 | Lessons from Automating Amazon with a Real Browser Profile | Automation developers | Edge CDP, login state, extension DOMs, fixed debugging port, cleanup | CrossMart Monitor | Outline needed |
| 07 | Building a Lightweight E-commerce Intelligence System Without a Backend Server | Indie hackers | GitHub Pages + JSON + scheduled local automation as cheap early architecture | CrossMart suite | Outline needed |
| 08 | What I Learned Turning Amazon Research Workflows into Small Decision Tools | Builders + operators | Product thinking: moving from dashboards to decisions | CrossMart suite | Outline needed |
| 09 | From Spreadsheet Pain to a CrossMart Toolkit: A Build-in-Public Recap | General Dev.to audience | Series recap, roadmap, and invitation to follow/try the tools | CrossMart suite | Outline needed |

## Publishing schedule

Use a 2-3 day cadence at the start, then slow slightly after the core tool posts.

| Slot | Timing | Article | Purpose |
|---|---|---|---|
| 1 | T+0 after final approval | 01 Monitor | Launch with the strongest completed story. |
| 2 | T+2 | 02 Selector | Move from monitoring to product selection. |
| 3 | T+4 | 03 Listing | Introduce AI generation after readers understand the data source. |
| 4 | T+7 | 04 Ops | Show the higher-value diagnosis layer. |
| 5 | T+10 | 05 Snapshot-first | Technical depth; useful for dev audience. |
| 6 | T+13 | 06 Real browser automation | Technical depth; CDP/extension lessons. |
| 7 | T+17 | 07 Backendless system | Architecture/cost angle for indie hackers. |
| 8 | T+21 | 08 Decision tools | Product-thinking article. |
| 9 | T+25 | 09 Build-in-public recap | Tie the series together and collect traffic. |

## CTA links

Use the current live links:

- CrossMart Monitor: https://charlescome1995-prog.github.io/crossmart-monitor/monitor.html
- CrossMart Selector: https://charlescome1995-prog.github.io/crossmart-selector/selection.html
- CrossMart Listing Builder: https://charlescome1995-prog.github.io/crossmart-listing/listing.html
- CrossMart Ops: https://charlescome1995-prog.github.io/crossmart-ops/ops.html
- CrossMart Simulator: https://charlescome1995-prog.github.io/crossmart-simulator/simulator.html

## Article template

Each article should follow this structure:

1. Painful real workflow
2. Small concrete example
3. Architecture or method
4. One hard lesson / bug / tradeoff
5. What I would improve next
6. Soft CTA to the relevant CrossMart page

## Pre-publish checklist

- [ ] Keep `published: false` until explicit final approval.
- [ ] Verify all live links.
- [ ] Remove private credentials, local-only paths, tokens, and internal account details.
- [ ] Keep examples sanitized; no private customer/order/seller data.
- [ ] Add cover image if available.
- [ ] Decide whether to expose GitHub repo links or only live demos.
- [ ] Add a short comment at the end asking readers what they would monitor or automate.
