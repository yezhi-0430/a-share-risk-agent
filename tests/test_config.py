from sqlalchemy import inspect, text

from app.config import Settings
from app.database import create_tables, engine


def test_builds_postgresql_database_url() -> None:
    settings = Settings(
        _env_file=None,
        database_host="localhost",
        database_port=5432,
        database_name="a_share_risk_agent",
        database_user="a_share_agent",
        database_password="test-password",
    )

    assert settings.database_url.drivername == "postgresql+psycopg"
    assert settings.database_url.username == "a_share_agent"
    assert settings.database_url.password == "test-password"
    assert settings.database_url.database == "a_share_risk_agent"


def test_connects_to_database() -> None:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT current_database()"))

    assert result.scalar_one() == "a_share_risk_agent_test"


def test_database_contains_project_tables() -> None:
    create_tables()
    table_names = set(inspect(engine).get_table_names())

    assert {
        "stocks",
        "watchlists",
        "watchlist_items",
    }.issubset(table_names)


def test_tests_use_test_database() -> None:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT current_database()"))

    assert result.scalar_one() == "a_share_risk_agent_test"
