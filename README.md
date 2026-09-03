![ProofThread — accountable group memory for Telegram](docs/assets/proofthread-banner.svg)

# ProofThread

> **Turn fast-moving Telegram conversations into decisions that can be proved and work that gets finished.**

[![CI](https://github.com/Oluwafemi1x/proofthread-telegram-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/Oluwafemi1x/proofthread-telegram-bot/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB)](https://www.python.org/)
[![aiogram](https://img.shields.io/badge/aiogram-3.x-2CA5E0)](https://docs.aiogram.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

ProofThread is an open-source, privacy-first decision and accountability ledger for Telegram groups. Reply to the message where work or agreement began, capture it as a decision, action, or unanswered question, and ProofThread keeps the owner, deadline, status history, and a link back to the source.

It is deliberately **not another chat summarizer**. ProofThread does not need to ingest every conversation, guess what the group meant, or create an opaque AI memory. Every saved item is explicit, attributable, reviewable, and reversible.

## The problem

Telegram groups are excellent for fast conversation, but important outcomes disappear into the scroll:

- decisions are repeated because nobody can find the original agreement;
- requests have no owner or deadline;
- questions remain unanswered without an inbox;
- task lists lose the message that explains *why* the work exists; and
- summaries sound useful but are difficult to verify.

Generic summarizers and task bots already exist. ProofThread focuses on the underserved space between them: **human-confirmed operational memory with evidence and lifecycle**.

## What makes ProofThread different

| Typical group bot | ProofThread |
|---|---|
| Archives many or all messages | Stores only explicit ledger entries and a short replied-to excerpt |
| Produces a disposable summary | Maintains durable decisions, actions, and questions |
| Loses the source context | Links each record to its Telegram source message |
| Treats a task as a line of text | Tracks creator, owner, due date, state, and state-change events |
| Silently guesses intent | Requires a person to decide what becomes official group memory |
| Replaces an old decision | Preserves it as superseded and links the replacement |

## Features

- 🧭 **Decision ledger** — record group decisions and supersede them without erasing history.
- ✅ **Action ownership** — attach an owner, deadline, source message, and completion state.
- ❓ **Unanswered-question inbox** — keep important questions visible until resolved.
- 🔗 **Evidence links** — jump from a ledger item to the public or private supergroup source.
- 🧾 **State history** — created, completed, resolved, cancelled, and superseded events are retained.
- ⏰ **Due-soon reminders** — notify the original group or forum topic before an action is due.
- 👤 **Personal queue** — `/mine` shows actions assigned directly to the requesting user.
- 📌 **Follow-up digest** — build a compact list of open work and unanswered questions.
- 🗂️ **JSON export** — group administrators can take a structured copy of the ledger.
- 🧹 **Privacy deletion** — creators and administrators can remove an entry with `/forget`.
- 🌍 **Per-group timezone** — interpret deadlines in each group's working timezone.
- 🔐 **Authenticated webhooks** — verify Telegram's secret-token header in production mode.
- 🐳 **Portable deployment** — run locally, in Docker, or with a PostgreSQL database.
- 🧪 **Tested core** — parser, evidence links, record lifecycle, scoping, and export behaviour.

## Quick example

Reply to a message in the group:

```text
/decision We will launch the public beta on September 20.
```

Create a tracked action:

```text
/action 2026-09-18 @femi Prepare the release notes
```

Capture a question that must not disappear:

```text
/question Who will own production monitoring?
```

Then review the shared operational memory:

```text
/open
/mine
/ledger
/digest
```

## Command reference

| Command | Who can use it | Purpose |
|---|---|---|
| `/decision TEXT` | Member | Capture a decision, preferably as a reply |
| `/action DATE OWNER TEXT` | Member | Create an action; use `-` for no date/owner |
| `/question TEXT` | Member | Capture an unanswered question |
| `/ledger` | Member | Show the 15 most recent records |
| `/open` | Member | Show open actions and questions |
| `/mine` | Member | Show open actions linked to your Telegram ID |
| `/digest` | Member | Generate a follow-up digest |
| `/complete ID` | Creator, owner, admin | Complete an action |
| `/resolve ID` | Creator, owner, admin | Resolve a question |
| `/cancel ID` | Creator, owner, admin | Cancel an open record |
| `/supersede ID TEXT` | Creator, admin | Replace a decision while keeping history |
| `/settimezone ZONE` | Admin | Set an IANA timezone such as `Africa/Lagos` |
| `/export` | Admin | Download up to 100 ledger records as JSON |
| `/forget ID` | Creator, admin | Permanently delete a ledger record |
| `/privacy` | Member | Explain exactly what the bot stores |

Action syntax:

```text
/action YYYY-MM-DD @owner Task description
/action YYYY-MM-DD me Task assigned to yourself
/action - - Task without an owner or due date
```

## Architecture

```mermaid
flowchart TD
    T["Telegram group"] --> R["aiogram handlers"]
    R --> S["Ledger service"]
    S --> D["Async SQLAlchemy"]
    D --> DB[("SQLite or PostgreSQL")]
    S --> E["Evidence and lifecycle events"]
    J["Reminder scheduler"] --> S
    J --> T
```

The bot uses a layered design:

1. **Telegram handlers** parse commands, enforce chat-level permissions, and render responses.
2. **Ledger service** owns validation, state transitions, chat scoping, exports, and event creation.
3. **Persistence models** store group settings, ledger records, and lifecycle events.
4. **Reminder scheduler** queries due actions and sends a single due-soon notification.
5. **Deployment runtime** supports long polling for development and secret-validated webhooks for production.

Read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for design decisions,
[docs/THREAT_MODEL.md](docs/THREAT_MODEL.md) for the security and privacy boundaries, and
[docs/RESEARCH.md](docs/RESEARCH.md) for the honest product positioning.

## Privacy model

ProofThread can operate with Telegram Bot privacy mode enabled. It receives commands and replied-to messages that Telegram makes available to the bot; it does not require a silent full-chat archive.

For each explicit record it stores only:

- the group and forum-topic identifiers;
- the record text;
- at most 320 characters from the replied-to source;
- the source message ID/link;
- creator and optional owner identifiers/labels;
- deadline, status, and lifecycle timestamps; and
- auditable state-change events.

Review Telegram's official [Bot Features](https://core.telegram.org/bots/features) and [Bot API](https://core.telegram.org/bots/api) documentation before deployment. Operators are responsible for informing members, selecting an appropriate retention policy, securing the database, and complying with local law.

## Install locally

### 1. Create the Telegram bot

1. Open [@BotFather](https://t.me/BotFather).
2. Run `/newbot` and follow the prompts.
3. Copy the token and keep it secret.
4. Add the bot to a test group.
5. Leave privacy mode enabled for the explicit-capture workflow.

### 2. Install ProofThread

```bash
git clone https://github.com/Oluwafemi1x/proofthread-telegram-bot.git
cd proofthread-telegram-bot
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
Copy-Item .env.example .env
```

Linux/macOS:

```bash
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
cp .env.example .env
```

Put the BotFather token in `.env`:

```dotenv
PROOFTHREAD_TELEGRAM_BOT_TOKEN=your-real-token
```

Start the bot:

```bash
proofthread
```

## Run with Docker

```bash
cp .env.example .env
# Edit .env and add the BotFather token
docker compose up --build -d
docker compose logs -f bot
```

The named Docker volume keeps the SQLite database across container restarts.

## Production webhook mode

Set these values behind a public HTTPS endpoint:

```dotenv
PROOFTHREAD_MODE=webhook
PROOFTHREAD_WEBHOOK_BASE_URL=https://bot.example.com
PROOFTHREAD_WEBHOOK_PATH=/telegram/webhook
PROOFTHREAD_WEBHOOK_SECRET=generate-a-long-random-secret
PROOFTHREAD_WEB_HOST=0.0.0.0
PROOFTHREAD_WEB_PORT=8080
```

Telegram includes the configured secret in the `X-Telegram-Bot-Api-Secret-Token` header. ProofThread rejects webhook requests that do not match it.

## PostgreSQL

Install the optional driver:

```bash
pip install -e ".[postgres]"
```

Configure the async URL:

```dotenv
PROOFTHREAD_DATABASE_URL=postgresql+asyncpg://proofthread:password@database/proofthread
```

Version 0.1 creates tables automatically. Before a multi-instance production deployment, add a migration workflow such as Alembic and use a shared job lock for reminders.

## Development

```bash
pip install -e ".[dev]"
ruff check .
pytest --cov=proofthread --cov-report=term-missing
```

CI runs linting and tests on Python 3.11, 3.12, and 3.13, then builds the container image.
The 90% coverage gate applies to the deterministic domain, persistence, parsing, rendering,
and reminder core. Telegram transport integration tests are tracked separately on the roadmap.

## Known boundaries

- ProofThread can link only messages visible to the bot.
- Private basic groups do not expose the stable `/c/` link format available to private supergroups.
- `/mine` requires an action to be linked to the user's Telegram ID. `me` always creates that link; another username is linked when ProofThread can safely identify that user from the command context.
- The first release sends one due-soon reminder per action. Recurring and escalating reminders are planned.
- Export is intentionally capped at 100 recent records in v0.1.
- Automatic AI extraction is intentionally excluded from the trusted core. A future optional extractor must present suggestions for human confirmation and must never silently declare a decision official.

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md). High-value contribution areas include:

- natural-language deadline parsing;
- signed or hash-chained ledger exports;
- configurable retention and scheduled deletion;
- recurring reminders and escalation policies;
- forum-topic dashboards;
- optional human-confirmed AI extraction;
- Alembic migrations and multi-instance scheduling locks; and
- broader Telegram Bot API 10.x rich-message support.

## Contributing

Issues, design discussions, tests, documentation improvements, and pull requests are welcome. Start with [CONTRIBUTING.md](CONTRIBUTING.md), follow the [Code of Conduct](CODE_OF_CONDUCT.md), and report vulnerabilities through [SECURITY.md](SECURITY.md).

Maintainers can use the ready-to-publish copy and repository metadata in
[docs/LAUNCH_KIT.md](docs/LAUNCH_KIT.md).

## License

ProofThread is available under the [MIT License](LICENSE).

Created by [Oluwafemi Olawumi Steven](https://github.com/Oluwafemi1x).
