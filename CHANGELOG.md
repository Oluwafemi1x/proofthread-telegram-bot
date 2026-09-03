# Changelog

All notable changes to ProofThread follow [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added

- Production PostgreSQL driver installed by default.
- Versioned Alembic schema migrations with automatic startup upgrades.
- PostgreSQL 17 Docker Compose service with health checks and durable storage.
- Provider database URL normalization and a `proofthread-db` migration command.
- PostgreSQL deployment, backup, and restore documentation.

## [0.1.0] - 2026-09-03

### Added

- Evidence-linked decisions, actions, and unanswered questions.
- Owner and due-date parsing for action items.
- Completion, resolution, cancellation, and decision-supersession states.
- Creator, owner, and administrator authorization for state changes.
- Open-item, personal-action, recent-ledger, and digest views.
- Due-soon reminders.
- Administrator JSON export and privacy deletion.
- Per-group timezone configuration.
- SQLite default storage and PostgreSQL-ready async database configuration.
- Polling and authenticated webhook deployment modes.
- Docker, CI, automated tests, security policy, and contribution documentation.

[Unreleased]: https://github.com/Oluwafemi1x/proofthread-telegram-bot/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Oluwafemi1x/proofthread-telegram-bot/releases/tag/v0.1.0
