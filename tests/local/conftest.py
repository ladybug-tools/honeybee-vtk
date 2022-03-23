import pytest
from tempfile import TemporaryDirectory
from pathlib import Path


@pytest.fixture(scope='session')
def temp_folder():
    d = TemporaryDirectory()
    yield Path(d.name)
    d.cleanup()
