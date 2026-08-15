import pytest

from varys.config import load_settings


def test_unknown_varys_setting_fails_startup() -> None:
    with pytest.raises(ValueError, match="Unknown VARYS_ setting"):
        load_settings({"VARYS_UNEXPECTED": "value"})


def test_settings_parse_expected_values() -> None:
    settings = load_settings(
        {
            "VARYS_API_PORT": "8010",
            "VARYS_DATA_ROOT": "/var/lib/varys",
            "VARYS_LOG_LEVEL": "debug",
        }
    )

    assert settings.api_port == 8010
    assert str(settings.data_root) == "/var/lib/varys"
    assert settings.log_level == "DEBUG"


def test_database_configuration_requires_a_long_session_secret() -> None:
    with pytest.raises(ValueError, match="VARYS_SESSION_SECRET must be at least 32"):
        load_settings({"VARYS_DATABASE_URL": "postgresql://localhost/varys"})
