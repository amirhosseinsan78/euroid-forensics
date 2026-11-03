import os

os.environ.setdefault("PYTEST_QT_API", "pyside6")

import pytest

from euroid_forensics.synthetic import demo_assets


@pytest.fixture
def assets():
    return demo_assets()
