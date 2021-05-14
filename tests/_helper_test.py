"""Unit tests for the helper module."""

import pytest
from honeybee_vtk._helper import _check_tuple


def test_check_tuple():
    """Test all the functionalities of this method."""
    val = (1, 2, 3)

    with pytest.raises(TypeError):
        _check_tuple(val)

    with pytest.raises(AssertionError):
        _check_tuple(val, float)

    with pytest.raises(AssertionError):
        _check_tuple(val, int, 1)

    assert _check_tuple(val, int, max_val=4)

    val = (0.1, 0.2, 0.3)
    
    assert _check_tuple(val, float, 1)
