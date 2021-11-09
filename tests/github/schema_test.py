"""Unit test for the schema module."""

import pytest
from honeybee_vtk.vtkjs.schema import DataSet, DataSetResource

# TODO: more unit tests to be added to cover the whole schema


def test_default_legend_ranges():
    """Check default values of legend_ranges."""
    dr = DataSetResource(url='.')
    ds = DataSet(name='temp', httpDataSetReader=dr)
    assert ds.legends == []
