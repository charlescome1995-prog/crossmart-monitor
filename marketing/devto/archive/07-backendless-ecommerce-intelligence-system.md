---
title: Building a Lightweight E-commerce Intelligence System Without a Backend Server
published: false
description: How GitHub Pages, JSON files, and scheduled local automation can form a cheap early-stage intelligence system.
tags: githubpages, architecture, automation, indiehackers
cover_image: "
canonical_url: "
---

<!--
Dev.to draft skeleton / CrossMart content matrix.
Status: outline only. Expand before publishing.
Primary CTA: CrossMart suite
-->

Opening hook to write:

- Start with a concrete operator/developer pain point.
- Avoid sounding like a product ad in the first third.
- Use CrossMart as the practical example, not the whole story.

## The constraint

- No public backend server.
- No database at launch.
- Keep deployment cheap and inspectable.

## The architecture

- Scheduled local Python collectors.
- JSON output committed to GitHub.
- GitHub Pages renders static dashboards.

## Why this works early

- Small surface area.
- Easy rollback.
- Data is transparent.
- Good enough for internal tools.

## Where it breaks

- Not multi-user by default.
- Public JSON needs sanitization.
- Long-running jobs still need a real machine.

## Hard lesson

- A boring architecture ships faster than a perfect platform.

## What I would improve next

- Move secrets to GitHub Actions or local env.
- Add auth only when needed.
- Add cache/version metadata.

## Soft CTA

Try the related CrossMart page here: [CrossMart suite](https://charlescome1995-prog.github.io/crossmart-monitor/monitor.html).

Question for readers: what part of this workflow would you automate next?
