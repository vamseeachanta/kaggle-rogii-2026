# kaggle-rogii-2026 — Kaggle competition (deadline 2026-08-05)

This repo is nested inside workspace-hub for navigation but is governed by Kaggle competition rules.

## Data boundary
- Competition dataset lives on `/mnt/ace` (data/{raw,interim,processed} are symlinks, gitignored).
- NEVER commit dataset content. NEVER echo dataset rows into commits, PRs, or notebook outputs that get pushed.
- Kaggle ToS prohibits redistribution.

## Agent-context firewall
- Do NOT inherit workspace-hub private project memory; local `.claude/` is gitignored and scopes memory namespace.
- Free-compute environments (Kaggle notebooks) walk `Path.parent` to find repo root — assume that walk starts here.
