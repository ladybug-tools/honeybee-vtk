"""Helper functions for honeybee-vtk."""

from typing import Dict, List
from collections import defaultdict

from .types import PolyData


def separate_by_type(data: List[PolyData]) -> Dict:
    """Separate PolyData objects by type."""
    data_dict = defaultdict(lambda: [])

    for d in data:
        data_dict[d.type].append(d)

    return data_dict
