---
title: "Building a Lightweight E-commerce Intelligence System Without a Backend Server"
published: false
description: "How GitHub Pages, JSON snapshots, and scheduled local automation became a cheap early-stage architecture for CrossMart."
tags: githubpages, architecture, automation, ecommerce
series: CrossMart Build Notes
cover_image: ""
canonical_url: ""
---

<!--
Dev.to draft 05 / CrossMart launch traffic article
Status: ready for final human review, not yet published.
Primary CTA: CrossMart suite.
Merged duplicate angles: snapshot-first data + backendless architecture + build-in-public recap.
-->

A lot of internal tools do not need to start as SaaS products.

They need to answer one painful question reliably.

For CrossMart, the painful question was simple:

> What changed in the Amazon market, and what should I look at next?

That question eventually turned into several small tools:

- a competitor monitor
- a product opportunity selector
- an AI listing builder
- an operations diagnosis dashboard

But the architecture behind the first version stayed intentionally boring:

```text
scheduled local automation -> JSON snapshots -> GitHub Pages dashboard
```

No public backend server.

No database.

No user system.

No complicated deployment pipeline.

Just Python, JSON, GitHub Pages, and a real browser when needed.

The current public pages are here:

- [CrossMart Monitor](https://charlescome1995-prog.github.io/crossmart-monitor/monitor.html)
- [CrossMart Selector](https://charlescome1995-prog.github.io/crossmart-selector/selection.html)
- [CrossMart Listing Builder](https://charlescome1995-prog.github.io/crossmart-listing/listing.html)
- [CrossMart Ops](https://charlescome1995-prog.github.io/crossmart-ops/ops.html)

This post is a recap of the architecture: why it worked, where it is limited, and what I would change before turning it into something bigger.

---

## The constraint: ship something useful before building a platform

The early goal was not to build a polished SaaS product.

The goal was to make repetitive Amazon research less manual.

That matters because architecture follows the goal.

If the goal is a multi-user commercial platform, you probably need:

- auth
- database
- background jobs
- queueing
- user-specific storage
- billing
- permissions
- server monitoring

But if the goal is an early internal decision tool, you can often start much smaller.

The first CrossMart tools only needed:

- collect data on a schedule
- save the latest output
- preserve historical snapshots
- show a dashboard
- make the result shareable by link

GitHub Pages plus JSON was enough.

---

## The basic architecture

The pattern looks like this:

```text
Local Windows machine
        |
        | scheduled Python task
        v
Browser / files / seller-tool exports
        |
        | collectors and processors
        v
Timestamped snapshots
        |
        | normalize for frontend
        v
JSON data files
        |
        | git commit / push
        v
GitHub Pages static dashboard
```

Each tool has a slightly different collector, but the shape is similar.

For Monitor:

```text
Amazon pages -> ASIN and keyword snapshots -> rawData.json -> dashboard
```

For Selector:

```text
Seller-tool Excel export -> scoring engine -> selection-data.json -> dashboard
```

For Listing:

```text
Keyword -> benchmark ASIN extraction -> AI listing draft -> listing-data.json -> dashboard
```

For Ops:

```text
Competitor ASINs -> traffic/ad/review signals -> ops-data.json -> dashboard
```

The frontend does not need to know how the data was collected.

It only needs a stable JSON contract.

---

## Why snapshot-first data helped

The most useful design decision was saving snapshots instead of only keeping the latest result.

A simplified folder structure:

```text
processed/
  asin_B0XXXXXXX/
    latest.json
    snapshot_20260626_050000.json
    snapshot_20260626_110000.json
    snapshot_20260626_210000.json

  keyword_batana_oil/
    latest.json
    snapshot_20260626_050000.json
    snapshot_20260626_110000.json
    snapshot_20260626_210000.json
```

The dashboard reads a normalized data file, but the historical snapshots stay available for debugging and comparison.

This helped in three ways.

### 1. Debugging became easier

If the dashboard looked wrong, I could inspect the exact snapshot that produced it.

That made it easier to separate:

- collector bugs
- data normalization bugs
- frontend rendering bugs
- missing fields from the source page

Without snapshots, every bug feels like a mystery.

### 2. Change detection became a feature

Operators do not only care about the current number.

They care about what changed:

- price moved
- review count grew
- rank improved
- coupon appeared
- listing status changed
- sponsored placement appeared

That is only possible if the system remembers previous states.

### 3. The system could evolve safely

Collectors can be messy. Frontends should not be.

Snapshots let the backend preserve raw detail while a sync step creates clean frontend data.

That separation made the project much easier to extend.

---

## Why GitHub Pages was enough

GitHub Pages is not a database. It is not a backend. It is not a job runner.

But it is very good at hosting static dashboards.

The frontend can do something as simple as:

```js
const response = await fetch('./data/rawData.json?t=' + Date.now());
const data = await response.json();
renderDashboard(data);
```

That means deployment becomes simple:

1. generate JSON locally
2. commit updated data
3. push to GitHub
4. let GitHub Pages serve the latest dashboard

For an early internal tool, this has real advantages:

- no server bill
- no backend maintenance
- no auth layer to build too early
- easy rollback through git history
- shareable public demo links
- transparent data files

The boring architecture made it easier to ship.

---

## Where this architecture breaks

This architecture is useful, but it is not magic.

It has clear limits.

### Public JSON must be sanitized

If the dashboard is public, the JSON is public too.

That means no private credentials, customer data, sensitive seller data, or internal notes should be committed into frontend data files.

Static hosting makes data exposure easy to overlook.

### Local automation is still infrastructure

Even without a backend server, the local runner matters.

If a workflow depends on a real browser, browser extensions, login state, or scheduled tasks, then that machine is part of the system.

It needs:

- stable environment
- predictable browser profile
- scheduled task monitoring
- logs
- timeout handling
- cleanup scripts

No backend does not mean no operations.

It just moves the operational burden somewhere else.

### Multi-user workflows need a different design

GitHub Pages plus JSON is fine for a single operator or public demo.

It is not enough for:

- multiple users
- private dashboards
- per-user configs
- write-heavy workflows
- permissioned data
- real-time collaboration

At that point, a real backend becomes reasonable.

The key is not to build it before the workflow is proven.

---

## What I would do differently next time

This project grew from one monitor into a small toolkit. That created some lessons.

### Define data contracts earlier

At the start, it is tempting to let JSON evolve freely.

That is fast, but it can create frontend/backend drift.

A simple schema for each tool would help:

```json
{
  "updated_at": "2026-06-26T05:00:00Z",
  "items": [
    {
      "id": "B0XXXXXXX",
      "type": "asin",
      "metrics": {},
      "signals": {},
      "diff": {}
    }
  ]
}
```

Even a lightweight schema makes future changes safer.

### Separate public and private data from day one

Internal tools often start with local assumptions.

But once a page is public, those assumptions become risky.

I would create a stricter boundary earlier:

- raw private snapshots stay local
- sanitized frontend JSON is published
- credentials live only in environment variables or secrets
- public demos use safe example data

### Treat links as part of the product

When multiple static tools link to each other, URL structure matters.

A broken navigation link makes the whole system feel unreliable.

The CrossMart tools now share a clearer top-level link structure, but I should have standardized it earlier.

---

## The bigger product lesson

The main lesson was not technical.

It was that small decision tools are often better than one giant dashboard.

Each CrossMart page answers a different question:

- Monitor: what changed?
- Selector: what opportunities deserve attention?
- Listing Builder: how could we draft a better listing from market evidence?
- Ops: what competitor behavior should we investigate?

They share patterns, but they do not need to be one huge application yet.

That made the project easier to build and easier to explain.

---

## Final thought

If you are building an internal tool, you probably do not need the perfect architecture on day one.

You need a workflow that is:

- repeatable
- inspectable
- cheap to run
- easy to debug
- useful enough that someone comes back to it

For CrossMart, that meant Python collectors, snapshot-first data, JSON contracts, and GitHub Pages dashboards.

It is not the final architecture forever.

But it was the right architecture for learning fast.

You can explore the current CrossMart pages here:

- [CrossMart Monitor](https://charlescome1995-prog.github.io/crossmart-monitor/monitor.html)
- [CrossMart Selector](https://charlescome1995-prog.github.io/crossmart-selector/selection.html)
- [CrossMart Listing Builder](https://charlescome1995-prog.github.io/crossmart-listing/listing.html)
- [CrossMart Ops](https://charlescome1995-prog.github.io/crossmart-ops/ops.html)

If you are building a small automation tool, my advice is simple: start with the painful spreadsheet, save snapshots, make the output visible, and only add a backend when the workflow earns it.
