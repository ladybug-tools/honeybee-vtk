"""Helper functions to be used in other modules."""
from itertools import chain
from typing import Any, Union, List, Tuple


def _validate_input(val: Union[List, Tuple], val_type: Any, max_val: int = None) -> bool:
    """Validate if all values in the provided input are selected object type and
    less than a specific maximum value.

    Args:
        val: A list or a tuple
        val_type: Object type that you'd want as values in input. Examples are
            int or float.
        max_val: A number either integer or float. The values in the input shall be
            less than this number.

    Returns:
        A boolean value if True.
    """
    if not max_val:
        return all(list(map(lambda v: isinstance(v, val_type), val)))
    else:
        return all(list(map(lambda v: isinstance(v, val_type) and v < max_val, val)))


def get_min_max(val: List[List]) -> Tuple[float, float]:
    """Get minimum and maximum values from a list of lists.

    Args:
        val: A list of lists

    Returns:
        A tuple of minimum and maximum values.
    """
    result = list(chain(*val))
    return (min(result), max(result))


def get_line_count(file_path: str) -> int:
    """Get the number of non empty lines in a file.

    Args:
        file_path: File path.

    Returns:
        The number of non empty lines in the file.
    """
    with open(file_path) as fp:
        nonempty_line_count = len([line.strip("\n") for line in fp if line != "\n"])
    return nonempty_line_count
