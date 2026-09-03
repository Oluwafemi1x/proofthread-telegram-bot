# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| 0.1.x | Yes |

## Report a vulnerability

Do not open a public issue for a vulnerability involving authentication, authorization, data exposure, webhook validation, database integrity, or Telegram tokens.

Use GitHub's **Report a vulnerability** private security-advisory feature for this repository. Include:

- the affected version or commit;
- reproduction steps using synthetic data;
- the expected and observed behaviour;
- the potential impact; and
- a suggested mitigation, if available.

Do not include a live bot token, real chat content, personal information, or an operator's database.

## Operator responsibilities

- Keep the BotFather token and webhook secret outside source control.
- Use HTTPS and a long random webhook secret in production.
- Restrict database and backup access to the bot operator.
- Inform group members what is collected and why.
- Review `/export` and `/forget` permissions before deployment.
- Apply dependency and container updates promptly.
- Back up the database before upgrades.

See [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md) for the current boundaries and non-goals.

