"""Unit tests for the helper module."""

import pytest
from honeybee_vtk._helper import _validate_input


def test_check_tuple():
    """Test all the functionalities of this method."""
    val = (1, 2, 3)
    assert _validate_input(val, int, max_val=4)

    val = (0.1, 0.2, 0.3)
    assert _validate_input(val, float, 1)
    assert _validate_input(val, float)

    val = (1, 2, 3)
    assert not _validate_input(val, float)

    val = (1.2, 3.4, 5.4)
    assert not _validate_input(val, float, 1.0)
