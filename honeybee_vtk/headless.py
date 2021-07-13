"""
A module for using honeybee-vtk in non-interactive runtimes.
"""


class Display:
    def stop(self):
        pass


def try_headless(func):
    """
    A decorator for running a function in a headless environment.
    """
    def wrapped(*args, **kwargs):

        display = Display()

        try:
            from xvfbwrapper import Xvfb as X
            display = X()
            display.start()
        except ImportError:
            pass

        output = func(*args, **kwargs)

        display.stop()

        return output
    return wrapped
