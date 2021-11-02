"""Unit test for the types module."""

import pytest
import vtk
from honeybee.model import Model as HBModel
from honeybee_vtk.model import Model
from honeybee_vtk.types import ModelDataSet, PolyData, _get_data_range

file_path = r'tests/assets/gridbased.hbjson'
hb_model = HBModel.from_hbjson(file_path)
model = Model.from_hbjson(file_path)


def test_polydata_initialization():
    """Making sure all the any of the properties are not deleted."""

    polydata = PolyData()
    assert not polydata.identifier
    assert not polydata.type
    assert not polydata.name
    assert not polydata.boundary
    assert not polydata.construction
    assert not polydata.modifier
    assert not polydata._fields


def test_add_metadata_face():
    """Test adding metadata to a honeybee face."""
    polydata = PolyData()
    face = hb_model.rooms[0].faces[0]
    metadata = polydata._get_metadata(face)
    assert polydata.name == 'TestRoom_1..Face0'
    assert polydata.type == 'Wall'
    assert polydata.identifier == 'TestRoom_1..Face0'
    assert polydata.boundary == 'Outdoors'
    assert polydata.construction == 'Generic Exterior Wall'
    assert polydata.modifier == 'generic_wall_0.50'


def test_add_metadata_aperture():
    """Test adding metadata to a honeybee aperture."""
    polydata = PolyData()
    aperture = hb_model.rooms[0].faces[0].apertures[0]
    metadata = polydata._get_metadata(aperture)
    assert polydata.name == '47275c62-30dd-4f95-839e-075834ec6d99_1'
    assert polydata.type == 'Aperture'
    assert polydata.identifier == '47275c62-30dd-4f95-839e-075834ec6d99_1'
    assert polydata.boundary == 'Outdoors'
    assert polydata.construction == 'Generic Double Pane'
    assert polydata.modifier == 'g_material'


def test_add_metadata_shade():
    """Test adding metadata to a honeybee shade."""
    polydata = PolyData()
    shade = hb_model.rooms[0].faces[0].apertures[0].outdoor_shades[0]
    metadata = polydata._get_metadata(shade)
    assert polydata.name == '47275c62-30dd-4f95-839e-075834ec6d99_1_OutBorder0'
    assert polydata.type == 'Shade'
    assert polydata.identifier == '47275c62-30dd-4f95-839e-075834ec6d99_1_OutBorder0'
    assert polydata.construction == 'Generic Shade'
    assert polydata.modifier == 'generic_exterior_shade_0.35'


def test_get_metadata_face():
    """Test getting metadata out from a Polydata created from a honeybee face."""
    polydata = PolyData()
    face = hb_model.rooms[0].faces[0]
    metadata = polydata._get_metadata(face)
    num_of_cells = polydata.GetNumberOfCells()

    assert isinstance(metadata, dict)
    for key, value in metadata.items():
        assert key in ['Name', 'Boundary', 'Construction', 'Modifier']
        assert len(value) == num_of_cells
        assert value.count(key) == num_of_cells


def test_get_metadata_shade():
    """Test getting metadata out from a Polydata created from a honeybee shade."""
    polydata = PolyData()
    shade = hb_model.rooms[0].faces[0].apertures[0].outdoor_shades[0]
    metadata = polydata._get_metadata(shade)
    num_of_cells = polydata.GetNumberOfCells()

    assert isinstance(metadata, dict)
    for key, value in metadata.items():
        assert key in ['Name', 'Construction', 'Modifier']
        assert len(value) == num_of_cells
        assert value.count(key) == num_of_cells


def test_metadata_assignment():
    """Test whether metadata is being correctly assigned as cell data."""

    for ds in model:
        for polydata in ds.data:
            assert polydata.name == polydata.GetCellData(
            ).GetAbstractArray('Name').GetValue(0)

            if ds.name != 'Shade':
                assert polydata.boundary == polydata.GetCellData(
                ).GetAbstractArray('Boundary').GetValue(0)

            assert polydata.construction == polydata.GetCellData(
            ).GetAbstractArray('Construction').GetValue(0)

            assert polydata.modifier == polydata.GetCellData(
            ).GetAbstractArray('Modifier').GetValue(0)


def test_get_data_range():
    """Test that _get_data_range responds with expected values."""
    values = vtk.vtkFloatArray()
    for i in range(11, 20):
        values.InsertNextValue(i)

    # make sure auto_calculated range is returned it data_range is not provided
    assert _get_data_range('test', None, values) == (11, 19)
    with pytest.warns(Warning):
        _get_data_range('test', None, values)

    # make sure auto_calculated range is returned if min and max in data_range is None
    assert _get_data_range('test', [None, None], values) == (11, 19)
    with pytest.warns(Warning):
        _get_data_range('test', [None, None], values)

    # make sure auto_calculated min is used if data_range min is None
    assert _get_data_range('test', [None, 18], values) == (11, 18)
    with pytest.warns(Warning):
        _get_data_range('test', [None, 18], values)

    # make sure auto_calculated max is used if data_range max is None
    assert _get_data_range('test', [11, None], values) == (11, 19)
    with pytest.warns(Warning):
        _get_data_range('test', [11, None], values)

    # make sure exception is raised if min and max are 0
    with pytest.raises(ValueError):
        _get_data_range('test', [0, 0], values)

    # make sure exception is raised if min is greater than max
    with pytest.raises(ValueError):
        _get_data_range('test', [10, 9], values)

    # make sure exception is raised if min and max are the same
    with pytest.raises(ValueError):
        _get_data_range('test', [10, 10], values)

    # make sure when string array is used, simply data_range is returned
    values = vtk.vtkStringArray()
    assert _get_data_range('test', [0, 100], values) == (0, 100)


def test_model_dataset_initialization_with_polydata():
    polydata = PolyData()
    polydata.add_data([1, 2, 3], 'demo-data')
    md = ModelDataSet('test', [polydata])

    assert md.data == [polydata]
    assert md._color_by is None
