# Launch kit

## One-line pitch

Turn fast-moving Telegram conversations into decisions that can be proved and work that gets
finished.

## GitHub description

Privacy-first decision and accountability ledger for Telegram groups—capture evidence-linked
decisions, owned actions, unanswered questions, deadlines, and auditable state changes.

## Recommended repository topics

`telegram-bot`, `python`, `aiogram`, `open-source`, `decision-log`, `task-management`,
`accountability`, `privacy`, `sqlalchemy`, `community-tools`

## Launch post

**I built ProofThread: accountable group memory for Telegram.**

Important outcomes disappear in busy group chats. A decision gets repeated, a request never gains
an owner, or a question scrolls away unanswered. Summaries help people catch up, but they rarely
show what became official or where it came from.

ProofThread turns a replied-to Telegram message into one of three durable records: a decision, an
owned action, or an unanswered question. Every entry retains its source, creator, status, and—in the
case of actions—its owner and deadline. Decisions can be superseded without deleting history.

The trusted core is deliberately deterministic. The bot can work with privacy mode enabled and does
not need to archive the whole group or let an AI silently decide what people agreed to.

The first public release includes SQLite/PostgreSQL support, polling and authenticated webhooks,
due reminders, JSON export, Docker, CI, a threat model, and contributor-friendly issue templates.

I would especially welcome collaborators interested in natural-language dates, signed exports,
retention controls, Telegram forum topics, and human-confirmed extraction.

## Collaboration call

The most valuable early contributions are not cosmetic. Help strengthen migrations, privacy
controls, lifecycle verification, localization, multi-instance scheduling, and transport-level tests.
Each proposed feature should name the user problem and describe its privacy impact.

