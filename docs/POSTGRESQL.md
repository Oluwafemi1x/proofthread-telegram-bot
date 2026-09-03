# PostgreSQL operations

ProofThread supports PostgreSQL as its production database and SQLite as its zero-cost local
default. PostgreSQL preserves the ledger only when the hosting provider also provides durable
database storage; storing a connection URL in GitHub does not run or preserve a database.

## Run PostgreSQL locally at no hosting cost

Docker Compose starts PostgreSQL 17, waits for it to become healthy, applies every Alembic
migration, and then starts the bot:

```bash
cp .env.example .env
# Add the Telegram token to .env
docker compose up --build -d
docker compose logs -f bot
```

Set a stronger local password in `.env` if the database port is ever exposed:

```dotenv
POSTGRES_PASSWORD=generate-a-long-random-password
```

The `proofthread-postgres` Docker volume survives normal container replacement and restarts.
`docker compose down` keeps it; `docker compose down --volumes` permanently deletes it.

## Connect a managed PostgreSQL service later

Most providers expose a URL beginning with `postgres://` or `postgresql://`. ProofThread safely
normalizes either form to SQLAlchemy's asynchronous `postgresql+asyncpg://` driver.

Set the provider's URL as a secret environment variable:

```dotenv
PROOFTHREAD_DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DATABASE
PROOFTHREAD_AUTO_MIGRATE=true
```

Never commit the real URL. It commonly contains a database password.

## Migrations

The bot upgrades the schema to the latest migration at startup by default. Operators can disable
that behaviour and migrate in a separate release step:

```dotenv
PROOFTHREAD_AUTO_MIGRATE=false
```

```bash
proofthread-db head
```

Inspect the current migration and history:

```bash
alembic current
alembic history
```

For multiple bot instances, run migrations once as a release job rather than simultaneously in
every replica.

Databases created by ProofThread 0.1 before Alembic was introduced are detected and stamped at the
matching initial revision before newer migrations run. A partial legacy schema stops startup with
an error instead of guessing or deleting data.

## Backup and restore

Create a compressed PostgreSQL backup:

```bash
pg_dump --format=custom --file=proofthread.backup "$PROOFTHREAD_DATABASE_URL"
```

Restore it into an empty database:

```bash
pg_restore --clean --if-exists --no-owner --dbname="$PROOFTHREAD_DATABASE_URL" proofthread.backup
```

Test restoration periodically. A backup that has never been restored is not yet proven usable.
