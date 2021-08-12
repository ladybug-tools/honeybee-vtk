"""Unit test for the types module."""

from honeybee.model import Model as HBModel
from honeybee_vtk.types import PolyData
from honeybee_vtk.model import Model

file_path = r'tests/assets/gridbased.hbjson'
model = Model.from_hbjson(file_path)


def test_polydata_initialization():
    """Making sure all the any of the properties are not deleted."""

    polydata = PolyData()
    assert not polydata.identifier
    assert not polydata.type
    assert not polydata.display_name
    assert not polydata.boundary_condition
    assert not polydata.construction_display_name
    assert not polydata.modifier_display_name
    assert not polydata._fields


def test_metadata():
    """Test whether metadata is being correctly assigned as cell data."""

    for ds in model:
        for polydata in ds.data:
            assert polydata.display_name == polydata.GetCellData(
            ).GetAbstractArray('Name').GetValue(0)

            if ds.name != 'Shade':
                assert polydata.boundary_condition == polydata.GetCellData(
                ).GetAbstractArray('Boundary Condition').GetValue(0)

            assert polydata.construction_display_name == polydata.GetCellData(
            ).GetAbstractArray('Construction').GetValue(0)

            assert polydata.modifier_display_name == polydata.GetCellData(
            ).GetAbstractArray('Modifier').GetValue(0)
