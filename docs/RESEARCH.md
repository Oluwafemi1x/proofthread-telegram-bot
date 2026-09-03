# Product research and positioning

Research snapshot: 2026-09-03.

## Problem selected

Fast-moving Telegram groups regularly produce decisions, assignments, and important questions,
but Telegram's conversational timeline is not an operational system of record. The useful unit is
not another summary: it is a small, attributable object that retains its evidence and lifecycle.

## Existing landscape

The ecosystem already contains open-source chat summarizers and standalone task bots. Therefore,
ProofThread does **not** claim that decision logs, tasks, reminders, or summarization are individually
novel. Its product wedge is the combination of:

- explicit human confirmation instead of ambient interpretation;
- decisions, actions, and unanswered questions in one lifecycle-aware ledger;
- a source-message link and excerpt attached to each record;
- decision supersession without rewriting history;
- privacy-mode compatibility without archiving the full conversation; and
- structured export and deletion controls for group administrators.

## Why the design is feasible

Telegram's official Bot API supports commands, replies, forum topics, long polling, webhooks, and a
secret token header for authenticating webhook delivery. Telegram also documents privacy mode for
group bots, which fits ProofThread's explicit-capture model. The implementation uses aiogram's
current asynchronous dispatcher and webhook integration.

Primary references:

- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Telegram Bot Features](https://core.telegram.org/bots/features)
- [aiogram documentation](https://docs.aiogram.dev/en/latest/)

Examples confirming adjacent tools already exist:

- [Telegram-Summarize-Bot](https://github.com/dudynets/Telegram-Summarize-Bot)
- [Dynaflow Telegram task bot](https://dynaflow.de/ops/telegram.html)

## Positioning rule

Public descriptions should say ProofThread is differentiated, privacy-first, evidence-linked, and
human-confirmed. They should not say it is the world's first, universally needed, or the only bot of
its kind unless a reproducible, comprehensive market analysis later supports that claim.

