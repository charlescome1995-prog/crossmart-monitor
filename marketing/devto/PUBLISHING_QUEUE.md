# Dev.to Publishing Queue - CrossMart

Status: ready for human review / manual scheduling.

Important: no Dev.to / Forem API token was found in the current environment, so these articles have **not** been posted or scheduled externally.

All publishable drafts keep `published: false` until final review.

## Launch batch

| Slot | Planned date | Draft file | Dev.to title | Primary CTA | Status |
|---|---|---|---|---|---|
| 1 | 2026-06-27 | `01-amazon-competitor-monitor-python-edge-github-pages.md` | I Built an Amazon Competitor Monitor with Python, Edge CDP, and GitHub Pages | CrossMart Monitor | Ready for review |
| 2 | 2026-06-29 | `02-keyword-exports-product-opportunity-engine.md` | Turning Seller Tool Keyword Exports into a Product Opportunity Engine | CrossMart Selector | Ready for review |
| 3 | 2026-07-01 | `03-ai-amazon-listing-builder-competitor-asins.md` | Building an AI Amazon Listing Builder from Competitor ASINs | CrossMart Listing Builder | Ready for review |
| 4 | 2026-07-04 | `04-traffic-keywords-operations-diagnosis.md` | From Traffic Keywords to Competitor Operations Diagnosis | CrossMart Ops | Ready for review |

If approval happens later, preserve the cadence: T+0, T+2, T+4, T+7.

## Manual publishing steps

For each article:

1. Open Dev.to dashboard.
2. Create a new post.
3. Paste the full markdown from the draft file.
4. Keep or adjust the front matter.
5. Add a cover image if available.
6. Preview links and formatting.
7. Publish or schedule according to the table above.

## API publishing note

If a Dev.to / Forem API token becomes available later, use the API only after final approval.

Suggested environment variable names to check:

- `DEVTO_API_KEY`
- `DEV_TO_API_KEY`
- `FOREM_API_KEY`

Do not hardcode the token into any markdown, JavaScript, or committed script.

## Final pre-publish checks completed

- [x] 9 overlapping draft ideas consolidated into 4 launch articles.
- [x] 02-04 expanded from outlines into full English Dev.to drafts.
- [x] `published: false` preserved across the four launch drafts.
- [x] Live CTA links checked and returning HTTP 200.
- [x] Sensitive string scan completed for the four launch drafts: no tokens, local paths, personal account IDs, or private credentials found.
- [x] 05-09 duplicate/overlapping skeletons moved to `archive/`.

## Still optional before launch

- [ ] Add cover images.
- [ ] Decide whether to add GitHub repo links or only live demo links.
- [ ] Do one final human tone/positioning review.
