# Dev.to Launch Article Plan

## Positioning

Goal: use practical build notes to attract developers, indie hackers, and e-commerce operators into the CrossMart tool ecosystem without sounding like direct advertising.

Tone: field note / build-in-public / practical automation case study.

Primary CTA: link to the relevant CrossMart GitHub Pages tool near the end of each article.

Canonical planning file: `CONTENT_MATRIX.md`.

## Final four-article sequence

The original 9 draft angles had several overlaps. They have now been consolidated into 4 publishable articles, each with one protagonist, one angle, and one CTA.

1. **Amazon Competitor Monitor**
   - Draft file: `01-amazon-competitor-monitor-python-edge-github-pages.md`
   - Angle: Python + Edge CDP + GitHub Pages monitoring dashboard.
   - CTA: CrossMart Monitor.
   - Status: full Dev.to draft ready for final review.

2. **Keyword Spreadsheet to Product Opportunity Engine**
   - Draft file: `02-keyword-exports-product-opportunity-engine.md`
   - Angle: turning seller-tool keyword Excel exports into a ranked product selection list.
   - CTA: CrossMart Selector.
   - Status: full Dev.to draft ready for final review.

3. **Building an AI Listing Builder from Competitor ASINs**
   - Draft file: `03-ai-amazon-listing-builder-competitor-asins.md`
   - Angle: benchmark ASIN extraction + evidence-based LLM listing generation.
   - CTA: CrossMart Listing Builder.
   - Status: full Dev.to draft ready for final review.

4. **From Traffic Keywords to Operations Diagnosis**
   - Draft file: `04-traffic-keywords-operations-diagnosis.md`
   - Angle: traffic keywords, ad visibility, review signals, and real-browser automation as an operations diagnosis layer.
   - CTA: CrossMart Ops.
   - Status: full Dev.to draft ready for final review.

## Consolidated / archived angles

The previous 05-09 article ideas are not scheduled as standalone posts for this launch batch because they overlapped with the main four. Their useful material has been merged into the four articles above.

Archived source skeletons live in `archive/`:

- `05-snapshot-first-data-market-monitoring.md` → merged mainly into Article 01.
- `06-automating-amazon-real-browser-profile.md` → merged mainly into Article 04.
- `07-backendless-ecommerce-intelligence-system.md` → merged into Article 01 and archived architecture notes.
- `08-amazon-research-workflows-decision-tools.md` → merged mainly into Article 02.
- `09-crossmart-toolkit-build-in-public-recap.md` → not used as a standalone launch article.

## Suggested publishing rhythm

Use a 2-3 day cadence. This keeps momentum without flooding Dev.to with similar CrossMart posts.

| Slot | Date | Article | Purpose |
|---|---|---|---|
| 1 | 2026-06-27 | 01 Monitor | Launch with the strongest completed story and CrossMart Monitor CTA. |
| 2 | 2026-06-29 | 02 Selector | Move from monitoring to product selection. |
| 3 | 2026-07-01 | 03 Listing | Introduce AI generation after readers understand the data source. |
| 4 | 2026-07-04 | 04 Ops | Finish with the higher-value diagnosis layer. |

If final approval happens later, keep the same relative cadence: T+0, T+2, T+4, T+7.

## Live CTA links verified

- CrossMart Monitor: https://charlescome1995-prog.github.io/crossmart-monitor/monitor.html
- CrossMart Selector: https://charlescome1995-prog.github.io/crossmart-selector/selection.html
- CrossMart Listing Builder: https://charlescome1995-prog.github.io/crossmart-listing/listing.html
- CrossMart Ops: https://charlescome1995-prog.github.io/crossmart-ops/ops.html
- CrossMart Simulator: https://charlescome1995-prog.github.io/crossmart-simulator/simulator.html

## Draft checklist before publishing

- [x] Reduce 9 overlapping angles to 4 publishable posts.
- [x] Convert articles 02-04 from skeletons into full Dev.to drafts.
- [x] Keep `published: false` in all article front matter.
- [x] Verify live links return HTTP 200.
- [x] Scan final four drafts for private credentials, local paths, tokens, and internal account details.
- [ ] Add cover images if available.
- [ ] Get explicit final approval before publishing or scheduling externally.
- [ ] If using Dev.to API, set `published: false` for drafts or use scheduled publishing only after approval.
