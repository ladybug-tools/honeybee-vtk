import sys

import pytest


@pytest.fixture(scope='session', autouse=True)
def virtual_framebuffer():
    class Display:
        def stop(self):
            pass

    display = Display()

    try:
        from xvfbwrapper import Xvfb as X
        display = X()
        display.start()
    except ImportError:
        pass

    yield
    display.stop()
