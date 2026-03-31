from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool


def test_migration_fallback_derives_annual_target_from_weekly_hours() -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    with Session(engine) as session:
        session.execute(
            text(
                """
                CREATE TABLE working_time_models (
                    id INTEGER PRIMARY KEY,
                    tenant_id INTEGER NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    weekly_target_hours NUMERIC(5,2) NOT NULL,
                    annual_target_hours NUMERIC(7,2) NULL
                )
                """
            )
        )
        session.execute(
            text(
                """
                INSERT INTO working_time_models (id, tenant_id, name, weekly_target_hours, annual_target_hours)
                VALUES (1, 1, 'Fallback Modell', 40.00, NULL),
                       (2, 1, 'Bestehend', 38.50, 2002.00)
                """
            )
        )
        session.execute(
            text(
                """
                UPDATE working_time_models
                SET annual_target_hours = weekly_target_hours * 52
                WHERE annual_target_hours IS NULL
                """
            )
        )
        session.commit()

        rows = session.execute(
            text("SELECT id, annual_target_hours FROM working_time_models ORDER BY id")
        ).all()

    assert float(rows[0][1]) == 2080
    assert float(rows[1][1]) == 2002


def test_migration_script_removes_legacy_weekly_fields() -> None:
    migration_file = Path("backend/migrations/versions/20260331_0003_annual_target_authoritative.py")
    migration_source = migration_file.read_text()

    assert 'drop_column("working_time_models", "weekly_target_hours")' in migration_source
    assert 'drop_column("working_time_models", "default_workdays_per_week")' in migration_source


def test_migration_script_creates_default_holiday_sets_for_existing_holidays() -> None:
    migration_file = Path("backend/migrations/versions/20260331_0005_holiday_sets.py")
    migration_source = migration_file.read_text()

    assert "SELECT DISTINCT tenant_id FROM holidays" in migration_source
    assert "UPDATE holidays SET holiday_set_id = :holiday_set_id WHERE tenant_id = :tenant_id" in migration_source
    assert "UPDATE tenants SET default_holiday_set_id = :holiday_set_id WHERE id = :tenant_id" in migration_source
