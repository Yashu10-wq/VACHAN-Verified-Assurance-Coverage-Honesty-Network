"""
Tests for versioned SQL migration runner.
Tests file discovery, checksum integrity, error handling, and database idempotency.
"""

from pathlib import Path
import psycopg
import pytest
from app.core.config import get_settings
from app.core.exceptions import MigrationException
from app.db.migrations import (
    apply_migrations,
    compute_checksum,
    discover_migrations,
    get_applied_migrations,
)


def test_discover_migrations_structure():
    """Verifies discovery of standard versioned migration files."""
    migrations = discover_migrations()
    assert len(migrations) >= 1
    first = migrations[0]
    assert first.version == "0001"
    assert first.name == "create_migration_tracking"
    assert len(first.checksum) == 64


def test_checksum_computation_consistency():
    """Verifies that compute_checksum is deterministic and immune to whitespace variations."""
    sql1 = "CREATE TABLE test (id INT);"
    sql2 = "  CREATE TABLE test (id INT);  \n"
    assert compute_checksum(sql1) == compute_checksum(sql2)


def test_invalid_migration_filename_rejection(tmp_path: Path):
    """Verifies rejection of invalid migration filenames without version prefix."""
    bad_file = tmp_path / "invalid_name.sql"
    bad_file.write_text("SELECT 1;", encoding="utf-8")

    with pytest.raises(MigrationException) as excinfo:
        discover_migrations(tmp_path)
    assert "Invalid migration filename" in str(excinfo.value)


def test_duplicate_migration_version_rejection(tmp_path: Path):
    """Verifies rejection when two files share the same version prefix."""
    file1 = tmp_path / "0001_first.sql"
    file2 = tmp_path / "0001_second.sql"
    file1.write_text("SELECT 1;", encoding="utf-8")
    file2.write_text("SELECT 2;", encoding="utf-8")

    with pytest.raises(MigrationException) as excinfo:
        discover_migrations(tmp_path)
    assert "Duplicate migration version detected" in str(excinfo.value)


@pytest.mark.asyncio
async def test_migration_idempotency_live_database():
    """
    Verifies that applying migrations against Neon PostgreSQL is strictly idempotent.
    """
    settings = get_settings()
    conn_string = settings.get_database_url()

    try:
        async with await psycopg.AsyncConnection.connect(
            conn_string, connect_timeout=int(settings.DATABASE_CONNECT_TIMEOUT)
        ) as conn:
            # First check applied migrations contains 0001
            applied = await get_applied_migrations(conn)
            assert "0001" in applied

            # Running apply again should return empty list (no double application)
            newly_applied = await apply_migrations(conn)
            assert newly_applied == []
    except psycopg.OperationalError:
        pytest.skip("Neon Cloud PostgreSQL connection was unreachable during live test.")
