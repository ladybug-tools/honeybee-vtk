"""Helper functions to be used in other modules."""


def _check_tuple(val, val_type, max_val=None):
    """Check if all values in the tuple are selected object type.

    Args:
        color: User input for color value
        val_type: Object type that you'd want as values in a tuple. Examples are
            int or float.
        max_val: A number either integer or float. The values in the tuple shall be
            less than this number.

    Returns:
        A boolean value if True.
    """
    # Check if all values in tuple are of expected object type
    item_check = [isinstance(v, val_type) for v in val]

    # Check if all values are less than the maximum allowed value
    if max_val:
        val_check = [v < max_val for v in val]
    else:
        val_check = [True] * len(val)

    assert item_check.count(True) == len(val), (
        f'The values in tuple must be {val_type} type.'
        )

    assert val_check.count(True) == len(val), (
        f'The values in tuple must be less than {max_val}.'
        )

    return True
