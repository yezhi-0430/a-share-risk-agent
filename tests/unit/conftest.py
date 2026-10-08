import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


@pytest.fixture
def stock_session(monkeypatch):
    # Configure model imports without connecting to the application database.
    for name, value in {
        "DATABASE_HOST": "127.0.0.1",
        "DATABASE_PORT": "5432",
        "DATABASE_NAME": "day10_unit_test_only",
        "DATABASE_USER": "test_only",
        "DATABASE_PASSWORD": "test_only",
    }.items():
        monkeypatch.setenv(name, value)

    from app.database import Base, Stock

    unit_engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(unit_engine)
    try:
        with Session(unit_engine) as session:
            session.add_all(
                [
                    Stock(symbol="000001.SZ", name="本地保存的名称甲"),
                    Stock(symbol="600000.SH", name="本地保存的名称乙"),
                ]
            )
            session.commit()
            yield session
    finally:
        unit_engine.dispose()
