# Roadmap

## 0.2 — Operational depth

- Natural-language dates with explicit confirmation.
- Recurring reminders and escalation rules.
- Configurable retention with scheduled deletion.
- Forum-topic-specific digest commands.
- CSV export alongside the structured JSON format.
- Automated PostgreSQL backup verification examples.

## 0.3 — Verifiability

- Hash-chained lifecycle events.
- Signed ledger exports and offline verification.
- Source-message edit/deletion awareness where Bot API updates permit it.
- Admin review queue for destructive actions.

## 0.4 — Human-confirmed intelligence

- Optional pluggable extractor for a single replied-to message or selected thread.
- Strict structured output with confidence and explanation.
- Confirmation buttons before any suggestion becomes an official record.
- Provider-independent interface and self-hosted-model documentation.
- Evaluation corpus for extraction accuracy and false-positive measurement.

## 1.0 — Stable operations

- Backward-compatible schema and command guarantees.
- Migration compatibility checks across supported PostgreSQL releases.
- Multi-instance reminder locking.
- Localization framework.
- Administrator observability and health endpoints.
- Documented upgrade and rollback policy.

Roadmap items are proposals, not promises. Open an issue before implementing a major schema, privacy, or trust-boundary change.
