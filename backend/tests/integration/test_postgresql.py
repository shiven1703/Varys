import os

import pytest

from varys.db import check_database_readiness, upgrade_database


@pytest.mark.integration
def test_clean_postgresql_database_migrates_to_head() -> None:
    database_url = os.getenv("VARYS_TEST_DATABASE_URL")
    if database_url is None:
        pytest.skip("VARYS_TEST_DATABASE_URL is not configured")
    if not database_url.startswith(("postgresql://", "postgresql+psycopg://")):
        pytest.fail("VARYS_TEST_DATABASE_URL must use PostgreSQL")

    upgrade_database(database_url)

    assert check_database_readiness(database_url).ready is True
