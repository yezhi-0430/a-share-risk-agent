from app.config import Settings


def test_settings_reads_model_key_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-only-key")

    settings = Settings(
        _env_file=None,
        database_host="localhost",
        database_port=5432,
        database_name="test_db",
        database_user="test_user",
        database_password="test-password",
    )

    assert settings.dashscope_api_key.get_secret_value() == "test-only-key"
