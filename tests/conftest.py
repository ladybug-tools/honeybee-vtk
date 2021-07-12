import sys

import pytest


@pytest.fixture(scope='session', autouse=True)
def virtual_framebuffer():
    class Display:
        def stop():
            pass

    display = Display()

    is_linux = sys.platform.startswith('linux')

    if is_linux:
        from xvfbwrapper import Xvfb as X
        display = X()
        display.start()
    yield
    display.stop()
