import pytest
from xvfbwrapper import Xvfb as X


@pytest.fixture(scope='session', autouse=True)
def virtual_framebuffer():
    display = X()
    display.start()
    yield
    display.stop()
