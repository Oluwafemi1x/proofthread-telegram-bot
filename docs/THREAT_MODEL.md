# Threat model

## Assets

- Telegram bot token and webhook secret.
- Group identifiers and member identifiers.
- Decision, task, question, owner, deadline, and source-excerpt data.
- Ledger history, exports, database, and backups.

## Trust boundaries

1. Telegram sends updates to polling or the authenticated webhook endpoint.
2. Handlers translate Telegram identities and commands into service calls.
3. The service enforces chat scoping and valid state transitions.
4. SQLAlchemy writes to an operator-controlled database.
5. Administrators can export or delete group records.

## Primary risks and controls

| Risk | Current control |
|---|---|
| Forged webhook request | Telegram secret-token header validation |
| Token disclosure | Environment-only configuration and secret types |
| Cross-group record access | Every record lookup includes `telegram_chat_id` |
| Unauthorized state change | Creator, linked owner, or live admin check |
| Silent mass collection | Explicit commands; no full-chat listener |
| Oversized content abuse | Record text limited to 1,000 characters and excerpts to 320 |
| Ambiguous short IDs | Prefix lookup succeeds only for exactly one record |
| SQL injection | SQLAlchemy expression API; no user-built SQL strings |
| Accidental history loss | Supersession preserves old decisions; deletion is explicit |
| Duplicate reminder storms | One reminder timestamp and single-instance scheduler job |

## Residual risks

- A compromised Telegram administrator can export or delete records.
- A compromised host can read the bot token and database.
- Telegram source messages can be edited or deleted after capture.
- Database operators can alter records directly; exports are not yet signed.
- SQLite is unsuitable for high-write, horizontally scaled deployments.
- Username ownership can change; Telegram numeric IDs are stronger when available.

## Future hardening

- configurable retention enforcement;
- encryption-at-rest deployment guidance;
- hash-chained event history and signed exports;
- rate limiting per group and user;
- Alembic migrations;
- distributed scheduling locks; and
- structured security-event monitoring.

