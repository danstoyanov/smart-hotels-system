import os
from urllib.parse import urlsplit

import pytest


@pytest.fixture
def database_url():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        if os.environ.get("CI"):
            pytest.fail("CI requires TEST_DATABASE_URL")
        pytest.skip("Run scripts/test.ps1 for disposable PostgreSQL checks")
    name = urlsplit(url).path.lstrip("/")
    if not name.endswith("_test"):
        pytest.fail("TEST_DATABASE_URL must name a disposable database ending in _test")
    return url
