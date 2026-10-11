"""
Lightweight, versioned SQL migration runner for Neon Cloud PostgreSQL.
Does not use SQLAlchemy or Alembic.
Guarantees transactional execution, idempotency, checksum validation, and advisory locking.
"""

import argparse
import asyncio
import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import sys
from typing import List, Optional

# Ensure Windows asyncio compatibility with psycopg 3
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import psycopg

from app.core.config import get_settings
from app.core.exceptions import MigrationException
from app.core.logging import get_logger, setup_logging

logger = get_logger(__name__)

# Distinct PostgreSQL advisory lock key for InsureChain VoiceGuard migrations
MIGRATION_ADVISORY_LOCK_ID = 847291


@dataclass
class MigrationFile:
    version: str
    name: str
    path: Path
    checksum: str


@dataclass
class MigrationStatus:
    version: str
    name: str
    applied: bool
    applied_at: Optional[datetime]
    checksum_match: bool


def compute_checksum(content: str) -> str:
    """Computes SHA-256 checksum of SQL migration content."""
    return hashlib.sha256(content.strip().encode("utf-8")).hexdigest()


def get_migrations_directory() -> Path:
    """Returns the migrations directory path relative to repository layout."""
    base_dir = Path(__file__).resolve().parent.parent.parent
    migrations_dir = base_dir / "migrations"
    migrations_dir.mkdir(parents=True, exist_ok=True)
    return migrations_dir


def discover_migrations(migrations_dir: Optional[Path] = None) -> List[MigrationFile]:
    """
    Discovers all .sql migration files sorted lexicographically by version prefix.
    Expected format: 0001_description.sql
    """
    directory = migrations_dir or get_migrations_directory()
    sql_files = sorted(directory.glob("*.sql"), key=lambda p: p.name)

    migrations: List[MigrationFile] = []
    seen_versions = set()

    for file_path in sql_files:
        filename = file_path.name
        parts = filename.split("_", 1)
        if len(parts) < 2 or not parts[0].isdigit():
            raise MigrationException(
                f"Invalid migration filename '{filename}'. "
                f"Expected format: <version_number>_<description>.sql (e.g. 0001_create_migration_tracking.sql)"
            )
        version = parts[0]
        name = parts[1].replace(".sql", "")

        if version in seen_versions:
            raise MigrationException(f"Duplicate migration version detected: {version}")
        seen_versions.add(version)

        content = file_path.read_text(encoding="utf-8")
        checksum = compute_checksum(content)

        migrations.append(
            MigrationFile(
                version=version,
                name=name,
                path=file_path,
                checksum=checksum,
            )
        )

    return migrations


async def ensure_tracking_table(conn: psycopg.AsyncConnection) -> None:
    """Ensures the schema_migrations audit table exists."""
    sql = """
    CREATE TABLE IF NOT EXISTS schema_migrations (
        id SERIAL PRIMARY KEY,
        version VARCHAR(64) NOT NULL UNIQUE,
        name VARCHAR(255) NOT NULL,
        checksum VARCHAR(64) NOT NULL,
        applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_schema_migrations_version ON schema_migrations (version);
    """
    async with conn.cursor() as cur:
        await cur.execute(sql)


async def get_applied_migrations(conn: psycopg.AsyncConnection) -> dict:
    """Retrieves applied migrations as a mapping of version -> dict of details."""
    await ensure_tracking_table(conn)
    sql = "SELECT version, name, checksum, applied_at FROM schema_migrations ORDER BY version ASC;"
    async with conn.cursor() as cur:
        await cur.execute(sql)
        rows = await cur.fetchall()
        return {
            row[0]: {
                "name": row[1],
                "checksum": row[2],
                "applied_at": row[3],
            }
            for row in rows
        }


async def check_migration_status(conn: psycopg.AsyncConnection) -> List[MigrationStatus]:
    """Checks the status of all discovered migrations against the database."""
    available = discover_migrations()
    applied = await get_applied_migrations(conn)

    statuses: List[MigrationStatus] = []
    for mig in available:
        if mig.version in applied:
            app_data = applied[mig.version]
            checksum_match = mig.checksum == app_data["checksum"]
            statuses.append(
                MigrationStatus(
                    version=mig.version,
                    name=mig.name,
                    applied=True,
                    applied_at=app_data["applied_at"],
                    checksum_match=checksum_match,
                )
            )
        else:
            statuses.append(
                MigrationStatus(
                    version=mig.version,
                    name=mig.name,
                    applied=False,
                    applied_at=None,
                    checksum_match=True,
                )
            )
    return statuses


async def apply_migrations(conn: psycopg.AsyncConnection) -> List[str]:
    """
    Applies unapplied migrations transactionally under an advisory lock.
    Returns list of newly applied versions.
    """
    # 1. Acquire PostgreSQL advisory lock to prevent concurrent runs
    logger.info("Acquiring migration advisory lock (%s)...", MIGRATION_ADVISORY_LOCK_ID)
    async with conn.cursor() as cur:
        await cur.execute("SELECT pg_advisory_lock(%s);", (MIGRATION_ADVISORY_LOCK_ID,))

    applied_versions: List[str] = []
    try:
        await ensure_tracking_table(conn)
        available = discover_migrations()
        applied = await get_applied_migrations(conn)

        for mig in available:
            if mig.version in applied:
                app_data = applied[mig.version]
                if mig.checksum != app_data["checksum"]:
                    logger.warning(
                        "Migration %s checksum mismatch! Expected: %s, Found: %s",
                        mig.version,
                        app_data["checksum"],
                        mig.checksum,
                    )
                continue

            logger.info("Applying migration %s: %s...", mig.version, mig.name)
            sql_content = mig.path.read_text(encoding="utf-8")

            # Execute migration in a transaction
            async with conn.transaction():
                async with conn.cursor() as cur:
                    await cur.execute(sql_content)
                    await cur.execute(
                        """
                        INSERT INTO schema_migrations (version, name, checksum, applied_at)
                        VALUES (%s, %s, %s, CURRENT_TIMESTAMP);
                        """,
                        (mig.version, mig.name, mig.checksum),
                    )

            logger.info("Successfully applied migration %s.", mig.version)
            applied_versions.append(mig.version)

        return applied_versions

    except Exception as exc:
        logger.error("Migration execution failed: %s", exc)
        raise MigrationException(f"Migration execution failed: {type(exc).__name__}") from exc
    finally:
        # 2. Release advisory lock
        async with conn.cursor() as cur:
            await cur.execute("SELECT pg_advisory_unlock(%s);", (MIGRATION_ADVISORY_LOCK_ID,))
        logger.info("Released migration advisory lock.")


async def run_cli() -> None:
    """CLI runner entrypoint."""
    setup_logging()
    parser = argparse.ArgumentParser(description="InsureChain VoiceGuard Migration Runner")
    parser.add_argument(
        "action",
        choices=["apply", "status"],
        help="Action to perform: 'apply' applies pending migrations; 'status' lists migration state.",
    )
    args = parser.parse_args()

    settings = get_settings()
    conn_string = settings.get_database_url()

    logger.info("Connecting to Neon PostgreSQL (%s)...", settings.get_sanitized_database_host())
    async with await psycopg.AsyncConnection.connect(conn_string) as conn:
        if args.action == "status":
            statuses = await check_migration_status(conn)
            print("\nMigration Status Report:")
            print("-" * 75)
            print(f"{'Version':<10} {'Name':<35} {'Applied':<10} {'Status':<15}")
            print("-" * 75)
            for s in statuses:
                status_str = "OK" if s.checksum_match else "CHECKSUM MISMATCH"
                applied_str = "YES" if s.applied else "PENDING"
                print(f"{s.version:<10} {s.name:<35} {applied_str:<10} {status_str:<15}")
            print("-" * 75)
        elif args.action == "apply":
            applied = await apply_migrations(conn)
            if applied:
                print(f"\nSuccessfully applied {len(applied)} migration(s): {', '.join(applied)}")
            else:
                print("\nDatabase is already up to date. No pending migrations.")


if __name__ == "__main__":
    asyncio.run(run_cli())
