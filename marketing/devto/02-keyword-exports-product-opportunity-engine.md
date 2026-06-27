---
title: Turning Seller Tool Keyword Exports into a Product Opportunity Engine
published: false
description: How I turned messy Amazon keyword spreadsheets into a ranked product selection workflow.
tags: amazon, ecommerce, data, automation
cover_image: "
canonical_url: "
---

<!--
Dev.to draft skeleton / CrossMart content matrix.
Status: outline only. Expand before publishing.
Primary CTA: CrossMart Selector
-->

Opening hook to write:

- Start with a concrete operator/developer pain point.
- Avoid sounding like a product ad in the first third.
- Use CrossMart as the practical example, not the whole story.

## The spreadsheet problem

- Keyword exports are useful but overwhelming.
- Operators need prioritization, not just rows.
- The key question: which product opportunity deserves attention first?

## What the engine reads

- Search volume, SPR, competition, concentration, ranking changes, price, margin-related fields.
- Normalize changing date columns before scoring.

## Scoring opportunities

- Separate blue ocean, red ocean, differentiation, and follow strategies.
- Use weighted scoring instead of a single magic metric.
- Explain why a product was recommended.

## Building the static dashboard

- Excel input -> Python normalization -> selection-data.json -> GitHub Pages.
- Filters and sorting make the output usable.

## Hard lesson

- Seller tool exports change column names over time.
- A resilient import layer matters more than a pretty dashboard.

## What I would improve next

- Add historical weekly comparison.
- Add reason codes for each score.
- Connect selected products to listing generation.

## Soft CTA

Try the related CrossMart page here: [CrossMart Selector](https://charlescome1995-prog.github.io/crossmart-selector/selection.html).

Question for readers: what part of this workflow would you automate next?
