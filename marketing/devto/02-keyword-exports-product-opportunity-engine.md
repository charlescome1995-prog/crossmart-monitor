---
title: "Turning Seller Tool Keyword Exports into a Product Opportunity Engine"
published: false
description: "A practical build note on converting messy Amazon keyword spreadsheets into a ranked product selection dashboard."
tags: python, data, ecommerce, automation
series: CrossMart Build Notes
cover_image: ""
canonical_url: ""
---

<!--
Dev.to draft 02 / CrossMart launch traffic article
Status: ready for final human review, not yet published.
Primary CTA: CrossMart Selector.
Merged duplicate angles: product opportunity scoring + decision-tool thinking.
-->

Most Amazon product research starts with an export button.

You open a seller research tool, type a seed keyword, download an Excel file, and suddenly you have thousands of rows: search volume, rank history, competition, price signals, conversion hints, category data, and a dozen columns whose names change depending on the week.

The problem is not that the data is missing.

The problem is that the data is too flat.

A spreadsheet can tell you that a keyword has search volume. It can tell you that a product has competitors. It can show you 30,000 rows. But it does not answer the operator question:

> Which opportunities are actually worth looking at first?

That was the reason I built **CrossMart Selector**.

It is a small tool that turns exported Amazon keyword spreadsheets into a ranked product opportunity list. The goal is not to replace human judgment. The goal is to make the first pass faster, more consistent, and less dependent on staring at Excel until every row looks the same.

You can try the current dashboard here:

👉 [CrossMart Selector](https://charlescome1995-prog.github.io/crossmart-selector/selection.html)

This post breaks down the approach: how the data is normalized, how I think about scoring, what went wrong, and why I prefer explainable filtering over a magic AI recommendation.

---

## The real workflow problem

When people talk about product selection, they often make it sound like one metric is enough:

- high search volume
- low competition
- good margin
- rising trend
- weak competitors
- low review count

In practice, none of those signals is enough on its own.

A keyword with huge search volume may be too competitive. A low-competition keyword may have no demand. A product with good margin may be dominated by a few strong brands. A product with weak competitors may still be hard to differentiate.

So the first version of the tool had one job:

> Turn a messy export into a short, explainable shortlist.

That means the system needs to do three things:

1. normalize changing spreadsheet columns
2. calculate useful opportunity signals
3. show why each row was selected

If the tool only outputs a score, operators will not trust it. The score has to come with evidence.

---

## The input: seller-tool Excel exports

The input is intentionally boring: an Excel file exported from a seller research workflow.

A typical file may include fields like:

- keyword
- monthly search volume
- ranking change
- search purchase ratio / SPR-like fields
- number of competing products
- demand-supply ratio
- price range
- review distribution
- category information
- concentration metrics
- date-based rank columns

The annoying part is that exports are not stable contracts.

A column may be named with a date this week, then a different date next week. For example, rank or search-volume columns can include the export date in the header.

That means the import layer cannot simply assume exact names forever.

The selector has to normalize columns before doing any analysis.

A simplified example:

```python
# Pseudocode
for column in excel_columns:
    if re.match(r"\d{8}rank", column):
        rename[column] = "rank_latest"

    if re.match(r"\d{8}search_volume", column):
        rename[column] = "monthly_search_latest"

frame = frame.rename(columns=rename)
```

This is not glamorous, but it is the difference between a tool that works once and a tool that survives the next export.

The first lesson was simple:

> Data normalization is part of the product, not just plumbing.

---

## Four opportunity buckets

Instead of giving every row one generic score, I wanted the tool to support different product-selection strategies.

The current version groups opportunities into four practical buckets.

### 1. Blue ocean

These are products or keywords where demand exists but competition looks relatively softer.

Signals might include:

- reasonable search volume
- lower competition
- lower concentration
- weaker visible competitors
- room for better positioning

This does not mean "easy." It means "worth investigating before the obvious red ocean terms."

### 2. Red ocean

These are competitive but potentially valuable opportunities.

A red ocean keyword may have:

- high search volume
- strong revenue potential
- many competitors
- higher review thresholds
- more aggressive advertising

The point is not to avoid red oceans. The point is to know what kind of fight you are entering.

### 3. Differentiation

Some opportunities are not attractive because the market is empty. They are attractive because the existing products look similar.

Differentiation signals can include:

- repeated product formats
- weak copywriting
- similar images
- missing use cases
- poor feature segmentation

This bucket is useful because not every opportunity is a pricing opportunity. Some are positioning opportunities.

### 4. Follow strategy

Sometimes the right move is not invention. It is fast, disciplined following.

A follow-style opportunity may show:

- validated demand
- clear leading products
- understandable customer expectations
- a product form that can be sourced or improved

This is especially useful for operators who want to reduce uncertainty.

---

## Scoring without pretending it is magic

The selector uses weighted scoring to make the first shortlist.

A simplified scoring model looks like this:

```python
score = (
    indicator_score * 0.40 +
    margin_score * 0.25 +
    heat_score * 0.20 +
    competition_score * 0.15
)
```

The exact weights can change, but the structure matters.

I do not want one metric to dominate the decision. A good opportunity needs a balance of:

- demand
- commercial potential
- manageable competition
- category fit
- strategy fit

The frontend then shows the result as a ranked list with filters.

Users can sort by score, margin, strategy, or recommendation level.

That makes the output more useful than a raw spreadsheet because it supports questions like:

- show me blue ocean ideas first
- show me high-score items with reasonable competition
- show me products that need a differentiation strategy
- show me items worth watching but not acting on yet

The goal is to reduce the first-pass review from thousands of rows to a manageable queue.

---

## The dashboard architecture

The architecture follows the same pattern as the rest of CrossMart:

```text
Excel export
    |
    v
Python normalization and scoring
    |
    v
selection-data.json
    |
    v
GitHub Pages dashboard
```

The frontend is static. It loads JSON and renders the current shortlist.

That is enough for an early tool because the heavy work happens before the page loads.

I like this separation:

- Python handles messy files and scoring
- JSON becomes the contract
- the frontend focuses on reading, filtering, and explaining

A static dashboard is not always the right answer, but it is excellent for early internal tools.

If the JSON file is valid, the page works.

---

## The hard lesson: changing exports break tools quietly

The hardest bug in this kind of workflow is not a dramatic crash.

It is when the tool still runs, but silently produces bad output because one column changed.

For example:

- a date-based rank column gets a new date
- a seller tool changes a column name
- an empty column appears before an important field
- the export format changes for a different category

That is why import validation matters.

Before scoring, the tool should be able to say:

- these required fields were found
- these fields were normalized
- these optional fields are missing
- these rows were skipped
- here is why a row received its score

This is also why I prefer explicit scoring over a black-box AI answer at this stage.

AI can help explain and summarize later. But the first pass should be deterministic enough to debug.

---

## Why this is not just an AI problem

It is tempting to throw the whole spreadsheet into an LLM and ask, "What should I sell?"

That can produce a nice-looking answer, but it is not reliable enough for product selection.

The better pattern is:

1. use code to clean and score structured data
2. use rules to create an explainable shortlist
3. use AI later to summarize, compare, or generate hypotheses

AI is useful after the data has been shaped.

For example, after CrossMart Selector identifies a shortlist, AI could help answer:

- what customer use cases appear across these products?
- what differentiation angles are plausible?
- what listing claims should be avoided?
- what benchmark products should be used for listing generation?

But the shortlist itself should not be a mystery.

---

## What I would improve next

The current version is useful, but there are obvious improvements.

### Historical comparison

A single export is a snapshot. Weekly exports would show movement.

I want the selector to answer:

- which opportunities are improving?
- which keywords are getting more competitive?
- which products are gaining visibility?
- which categories are cooling down?

### Better reason codes

Each recommendation should have a short explanation.

For example:

```text
Highly recommended because:
- strong monthly search volume
- moderate competition
- low concentration
- good strategy fit: differentiation
```

This makes the tool easier to trust.

### Connection to listing generation

The natural next step is connecting selected opportunities to a listing builder.

If a product opportunity looks good, the next question is:

> What would a strong listing look like for this opportunity?

That is why CrossMart Selector connects conceptually with CrossMart Listing Builder.

---

## Final thought

A spreadsheet export is not a decision tool by itself.

It is raw material.

The useful layer is the one that turns rows into a shortlist, a strategy, and a reason to investigate further.

That is what I wanted CrossMart Selector to do: not predict the perfect product, but make product research less random.

You can try the current version here:

👉 [CrossMart Selector](https://charlescome1995-prog.github.io/crossmart-selector/selection.html)

In the next article, I will write about the next step in the workflow: using competitor ASINs as structured input for an AI Amazon listing builder.
