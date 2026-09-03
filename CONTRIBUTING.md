# Contributing to ProofThread

Thank you for helping build accountable, privacy-respecting group tools.

## Before opening a pull request

1. Search existing issues and discussions.
2. Open an issue for a substantial feature or data-model change.
3. Keep the trusted core deterministic. AI-generated suggestions must require human confirmation.
4. Do not expand message collection without a documented privacy need and administrator opt-in.
5. Never include Telegram tokens, chat exports, real member data, or database files.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

## Quality checks

Run these before submitting:

```bash
ruff check .
pytest --cov=proofthread --cov-report=term-missing
docker build -t proofthread:test .
```

## Pull-request expectations

- Describe the problem, not only the code change.
- Include tests for new behaviour and failure paths.
- Update README, architecture, security, or command documentation when relevant.
- Keep state transitions and authorization decisions in the service/handler boundary.
- Use clear, imperative commit messages.
- Prefer focused pull requests that reviewers can reason about safely.

## Good first contributions

- More parser and rendering tests.
- Improved accessibility and localization.
- Database migration scaffolding.
- Retention-policy implementation.
- Deployment examples for common hosting platforms.

By participating, you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

