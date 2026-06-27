# Dev.to Content Matrix for CrossMart

Goal: turn the CrossMart build process into a compact Dev.to launch series that attracts developers, indie hackers, and Amazon/e-commerce operators without sounding like hard advertising.

Working principle: each article teaches one practical thing, then softly points readers to the relevant CrossMart page.

## Final decision

The original content pool had 9 angles, but several were overlapping architecture/product-thinking variants. For the first launch batch, the matrix is consolidated into **4 publishable articles**.

The remaining 5 angles are archived as source material and not scheduled as standalone Dev.to posts.

## Duplicate cleanup logic

| Overlap risk | Cleanup decision |
|---|---|
| Monitor build story vs snapshot-first data architecture | Keep Article 01 as the Monitor protagonist and include snapshot-first lessons inside it. |
| Real-browser automation vs Ops implementation | Merge real-browser automation lessons into Article 04, where they support the operations-diagnosis workflow. |
| Backendless architecture vs individual tool posts | Keep GitHub Pages / JSON / no-backend architecture as supporting context, not a standalone launch post. |
| Selector vs decision-tool product thinking | Merge decision-tool framing into Article 02: keyword export becomes ranked opportunity decisions. |
| Suite recap vs feature list | Drop the recap from the first batch to avoid repetitive CrossMart promotion. |

## Final four-article sequence

| # | Working title | Primary audience | Core angle | Primary CTA | Status |
|---|---|---|---|---|---|
| 01 | I Built an Amazon Competitor Monitor with Python, Edge CDP, and GitHub Pages | Developers + e-commerce operators | Build-in-public case study for CrossMart Monitor; includes snapshot-first monitoring and lightweight static-dashboard architecture. | CrossMart Monitor | Full draft ready for final review |
| 02 | Turning Seller Tool Keyword Exports into a Product Opportunity Engine | Amazon operators + indie hackers | How keyword spreadsheets become ranked, explainable product opportunities. | CrossMart Selector | Full draft ready for final review |
| 03 | Building an AI Amazon Listing Builder from Competitor ASINs | Operators + AI builders | Extract competitor patterns first, then generate structured Amazon listing drafts. | CrossMart Listing Builder | Full draft ready for final review |
| 04 | From Traffic Keywords to Competitor Operations Diagnosis | Amazon operators + automation developers | Traffic source, ad-insight, review analysis, and browser automation as an operations diagnosis dashboard. | CrossMart Ops | Full draft ready for final review |

## Archived source material

These files are kept under `archive/` for future reuse, but should not be published as part of this launch batch:

- `archive/05-snapshot-first-data-market-monitoring.md`
- `archive/06-automating-amazon-real-browser-profile.md`
- `archive/07-backendless-ecommerce-intelligence-system.md`
- `archive/08-amazon-research-workflows-decision-tools.md`
- `archive/09-crossmart-toolkit-build-in-public-recap.md`
- `archive/05-backendless-ecommerce-intelligence-system.md`

## Publishing schedule

Use a 2-3 day cadence at the start. If approval happens after 2026-06-27, shift the dates while preserving the spacing.

| Slot | Planned date | Relative timing | Article | Purpose |
|---|---|---|---|---|
| 1 | 2026-06-27 | T+0 | 01 Monitor | Launch with the strongest completed story. |
| 2 | 2026-06-29 | T+2 | 02 Selector | Move from monitoring to product selection. |
| 3 | 2026-07-01 | T+4 | 03 Listing | Introduce AI generation after readers understand competitor data. |
| 4 | 2026-07-04 | T+7 | 04 Ops | Show the higher-value diagnosis layer. |

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

- [x] Keep `published: false` until explicit final approval.
- [x] Verify all live links return HTTP 200.
- [x] Remove private credentials, local-only paths, tokens, and internal account details from the four publishable drafts.
- [x] Keep examples sanitized; no private customer/order/seller data.
- [x] Give each article one primary CTA.
- [ ] Add cover image if available.
- [ ] Decide whether to expose GitHub repo links or only live demos.
- [ ] Get explicit approval before posting/scheduling externally.
