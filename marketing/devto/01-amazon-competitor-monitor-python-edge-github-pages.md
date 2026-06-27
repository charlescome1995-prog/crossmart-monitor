---
title: "I Built an Amazon Competitor Monitor with Python, Edge CDP, and GitHub Pages"
published: false
description: "A practical field note on turning repetitive Amazon competitor checks into a lightweight monitoring dashboard."
tags: python, automation, ecommerce, githubpages
cover_image: ""
canonical_url: ""
---

<!--
Dev.to draft 01 / CrossMart launch traffic article
Target audience: developers, indie hackers, e-commerce operators who like practical automation builds.
Goal: soft traffic to CrossMart Monitor without sounding like a hard ad.
Suggested publish slot: first launch article.
Primary CTA: CrossMart Monitor demo link near the end.
-->

Every Amazon operator eventually builds the same ugly spreadsheet.

You start with a few ASINs.

Then you add price.

Then rating.

Then review count.

Then Best Sellers Rank.

Then coupons, badges, Prime discounts, launch dates, keyword search positions, and whatever your favorite seller tool says about traffic keywords.

At first, checking all of this manually feels manageable. Open Amazon, search a keyword, check a few competitor products, paste numbers into a sheet.

But after a few days, the spreadsheet becomes stale. After a few weeks, nobody trusts it. And when a competitor suddenly changes price, activates a coupon, climbs a keyword result page, or gets a review spike, you usually notice too late.

So I built a small tool for myself: **CrossMart Monitor**.

It is not a huge SaaS product. It is a lightweight Amazon competitor monitoring system built with:

- Python
- Microsoft Edge + Chrome DevTools Protocol
- GitHub Pages
- JSON snapshots
- a small static dashboard
- scheduled local runs

The live dashboard is here:

👉 [CrossMart Monitor](https://charlescome1995-prog.github.io/crossmart-monitor/monitor.html)

This post is a practical breakdown of the build: what problem it solves, why I chose this architecture, what went wrong, and what I would do differently next.

---

## The real problem: competitor data changes quietly

For Amazon products, the obvious metrics are easy to understand:

- price
- star rating
- review count
- Best Sellers Rank
- product title
- product image

But the useful signals are often more operational:

- Did the competitor turn on a coupon?
- Did they join a deal?
- Did their review count grow faster than usual?
- Did their keyword search position move?
- Did a new sponsored product appear for the keyword?
- Did a product with fewer reviews start ranking above older products?
- Did a listing badge, discount, or status change?

These are small changes individually. Together, they explain a lot.

A manual check gives you a screenshot of the market. A monitor gives you a timeline.

That was the main design goal:

> Build a simple system that captures repeatable snapshots and makes changes visible.

---

## What CrossMart Monitor tracks

The first version tracks two kinds of objects.

### 1. ASIN-level monitoring

For selected Amazon products, it captures fields such as:

- title
- price
- rating
- review count
- Best Sellers Rank
- brand
- main image
- coupon status
- Prime discount
- deal activity
- listing status
- launch date when available
- traffic keyword data from seller tools when available

### 2. Keyword-level monitoring

For selected keywords, it opens Amazon search results and records the top products, grouped by type:

- natural ranking products
- sponsored products
- newer products worth watching

For each keyword, the dashboard can show which ASINs are appearing, their rank, their price, their rating, and whether the visible competitive set has changed.

This matters because Amazon competition is not only product-vs-product. It is keyword-vs-keyword, placement-vs-placement, and timing-vs-timing.

---

## The architecture

The architecture is intentionally boring.

```text
Local Windows machine
        |
        | scheduled Python task
        v
Microsoft Edge with logged-in seller tools
        |
        | Chrome DevTools Protocol
        v
Python collectors
        |
        | write snapshots
        v
JSON data files
        |
        | git commit / push
        v
GitHub Pages dashboard
```

There is no database in the first version.

There is no backend server for the public dashboard.

There is no user account system.

The public page just reads JSON and renders a static dashboard.

That constraint made the system easier to ship.

---

## Why Edge CDP instead of a normal scraping stack?

For this project, I wanted the browser to behave like the actual operator environment.

Many Amazon seller workflows depend on:

- logged-in sessions
- browser extensions
- seller research tools
- dynamic pages
- client-side rendered panels
- human-triggered UI states

A raw HTTP scraper is cleaner in theory, but it often misses what the operator actually sees.

So the collector talks to an existing Edge browser through Chrome DevTools Protocol.

The key idea is:

```python
# Pseudocode, simplified
browser = connect_to_edge(port=9225)
page = browser.open("https://www.amazon.com/dp/B0XXXXXXX")
page.wait_for_load()
html = page.evaluate("document.body.innerText")
metrics = extract_metrics(html)
save_snapshot(metrics)
```

In the real version, the browser is launched on a fixed debugging port and uses the normal local profile. That allows the system to reuse existing Amazon and seller-tool login states.

The important lesson: **for operator tools, the browser profile is part of the runtime environment**.

That sounds messy, but it matches reality.

---

## Snapshot-first data modeling

The most useful design decision was saving snapshots instead of only saving the latest result.

The structure looks roughly like this:

```text
processed/
  asin_B0XXXXXXX/
    latest.json
    snapshot_20260626_050000.json
    snapshot_20260626_110000.json
    snapshot_20260626_210000.json

  kw_makeup_remover/
    latest.json
    snapshot_20260626_050000.json
    snapshot_20260626_110000.json
    snapshot_20260626_210000.json
```

Each run creates a new snapshot. Then the sync step builds a dashboard-friendly `rawData.json` file.

The frontend does not need to know how the data was collected. It only needs a normalized data file.

That separation helped a lot:

- collectors can be messy
- snapshots can preserve raw details
- sync logic can normalize fields
- frontend rendering stays simple

This also makes debugging easier. If the dashboard looks wrong, I can inspect the exact snapshot that produced it.

---

## The dashboard is static on purpose

The frontend is a GitHub Pages page.

It loads JSON:

```js
const response = await fetch('./data/rawData.json?t=' + Date.now());
const data = await response.json();
renderDashboard(data);
```

Then it renders:

- ASIN cards / rows
- keyword result tables
- status badges
- change indicators
- small trend lines
- last updated time
- competitor metric summaries

This is not the fanciest architecture, but it has a huge advantage:

> If the data file exists, the dashboard works.

No cloud backend. No server bill. No authentication layer. No deployment complexity.

For an internal or early-stage tool, that is often enough.

---

## Change detection is more useful than raw data

The first version displayed the latest metrics. That was useful, but not enough.

The dashboard became much more valuable after adding comparisons:

- previous price vs current price
- previous review count vs current review count
- previous rank vs current rank
- previous status vs current status
- first-seen vs latest values

A simplified version looks like this:

```python
def diff_metric(current, previous, key):
    if not previous:
        return {"type": "new", "current": current.get(key)}

    old = previous.get(key)
    new = current.get(key)

    if old == new:
        return {"type": "same", "current": new}

    return {
        "type": "changed",
        "previous": old,
        "current": new,
    }
```

The lesson was simple:

> Operators do not want more numbers. They want to know what changed.

That changed the UI direction. The monitor became less like a data table and more like an alert surface.

---

## The annoying parts

This project had the usual automation problems.

### 1. Dynamic pages are not stable documents

Amazon pages change by marketplace, product type, session, and experiment group. Some fields appear as text. Some are hidden in scripts. Some are absent on certain listings.

So the extractor has to be defensive.

### 2. Browser extensions are even trickier

Seller-tool browser extensions often render dynamic panels. Sometimes the data is not present until you click something. Sometimes the DOM structure changes. Sometimes the extension is installed but not active on the page.

For example, a table that looks simple visually may be rendered as nested `div` elements instead of normal `table > tr > td` HTML.

That means extraction code has to be based on the actual DOM, not assumptions.

### 3. Scheduled browser automation needs housekeeping

A scheduled task that uses a real browser can slowly accumulate tabs, stale sessions, and half-loaded pages.

I had to add more practical guardrails:

- use one fixed browser debugging port
- reuse the same browser profile
- clean up tabs when needed
- increase timeouts for slow sync steps
- separate monitor runs from heavier operations runs

Not glamorous, but necessary.

---

## What I like about this approach

The best part is that the tool is small enough to understand.

The collection pipeline is just:

```text
open page -> extract -> save snapshot -> normalize -> render
```

That makes it easy to extend.

Want to add coupon detection? Add a field to the extractor, snapshot, sync, and UI.

Want to track launch date? Add it to the snapshot and render it when present.

Want keyword monitoring? Add a keyword collector and normalize its output.

Want an operations dashboard later? Reuse the same idea: collect, snapshot, compare, render.

This is why CrossMart is now growing into a small toolkit instead of a single page:

- [CrossMart Monitor](https://charlescome1995-prog.github.io/crossmart-monitor/monitor.html) — ASIN and keyword monitoring
- [CrossMart Selector](https://charlescome1995-prog.github.io/crossmart-selector/frontend/selection.html) — product opportunity selection
- [CrossMart Listing Builder](https://charlescome1995-prog.github.io/crossmart-listing/frontend/listing.html) — benchmark-based listing generation
- [CrossMart Ops](https://charlescome1995-prog.github.io/crossmart-ops/ops.html) — traffic and operations diagnosis

They all follow the same principle:

> Turn scattered marketplace signals into repeatable decision tools.

---

## What I would improve next

The current version works, but there are obvious next steps.

### Better alerting

A dashboard is useful when someone opens it. Alerts are useful when something important happens.

I want to add simple rules like:

- price changed by more than X%
- review count grew unusually fast
- keyword rank entered top 5
- competitor activated a coupon
- listing status changed

### Cleaner data contracts

Right now, the system is flexible but still evolving. A stricter schema would make the frontend and backend safer.

Something like:

```json
{
  "asin": "B0XXXXXXX",
  "snapshot_time": "2026-06-26T05:00:00Z",
  "metrics": {
    "price": 19.99,
    "rating": 4.6,
    "reviews": 1234,
    "bsr": 5678
  },
  "signals": {
    "coupon": true,
    "deal": false,
    "prime_discount": false
  }
}
```

### More explainable insights

The monitor can show that something changed. The next step is explaining why it might matter.

For example:

- competitor rank improved after coupon activation
- review velocity increased after price drop
- sponsored placement appeared before organic rank improved

That is where the tool becomes more than a tracker.

---

## Final thought

This project reminded me that useful automation does not always start with a big platform.

Sometimes it starts with a painful spreadsheet.

Then one script.

Then one JSON file.

Then one static dashboard.

If the workflow is repetitive, the data changes over time, and the decision depends on noticing those changes, it is probably worth monitoring.

That was the idea behind CrossMart Monitor.

If you are building tools for e-commerce operators, indie sellers, or internal teams, I think this snapshot-first architecture is a good starting point: simple, inspectable, and cheap to run.

You can try the current dashboard here:

👉 [CrossMart Monitor](https://charlescome1995-prog.github.io/crossmart-monitor/monitor.html)

I am still improving the system, so the next write-up will probably be about the product selection engine: how I turned exported keyword spreadsheets into a ranked opportunity list.
