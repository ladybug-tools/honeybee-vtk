"""Unit tests for the model module."""

import os
import shutil
import pytest
from ladybug.color import Color
from honeybee_vtk.model import Model
from honeybee_vtk.types import ModelDataSet, DataSetNames
from honeybee_vtk.vtkjs.schema import SensorGridOptions, DisplayMode


def test_write_html():
    """Test if an HTML file can be successfully written."""

    file_path = r'tests/assets/unnamed.hbjson'
    model = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Mesh)

    target_folder = r'tests/assets/temp'
    if os.path.isdir(target_folder):
        shutil.rmtree(target_folder)
    os.mkdir(target_folder)
    model.to_html(folder=target_folder, name='Model')
    html_path = os.path.join(target_folder, 'Model.html')
    assert os.path.isfile(html_path)
    shutil.rmtree(target_folder)


def test_write_vtkjs():
    """Test if a vtkjs file can be successfully written."""

    file_path = r'tests/assets/unnamed.hbjson'
    model = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Mesh)

    target_folder = r'tests/assets/temp'
    if os.path.isdir(target_folder):
        shutil.rmtree(target_folder)
    os.mkdir(target_folder)
    model.to_vtkjs(folder=target_folder, name='Model')
    html_path = os.path.join(target_folder, 'Model.vtkjs')
    assert os.path.isfile(html_path)
    shutil.rmtree(target_folder)


def test_properties():
    """Test properties of a model."""

    file_path = r'tests/assets/unnamed.hbjson'
    model = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Mesh)

    # model is an iterator object. Hence, we're using a for loop to test properties
    for dataset in model:
        assert isinstance(dataset, ModelDataSet)


def test_load_grids():
    """Test loading of grids from hbjson."""

    file_path = r'tests/assets/revit_model/model.hbjson'
    model = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Ignore)
    assert model.sensor_grids.data == []

    model = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Mesh)
    assert len(model.sensor_grids.data) == 15


def test_displaymode():
    """Test displaymode assignment of model and model objects."""

    file_path = r'tests/assets/unnamed.hbjson'
    model = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Mesh)

    # set display mode for model
    model.update_display_mode(DisplayMode.Shaded)

    # check display mode is assgined to all the objects in a model
    for dataset in model:
        assert dataset.display_mode == DisplayMode.Shaded

    # assign a different display model to the sensor grids
    model.sensor_grids.display_mode = DisplayMode.Wireframe
    with pytest.raises(AssertionError):
        for dataset in model:
            assert dataset.display_mode == DisplayMode.Shaded


def test_hbjson_vtk_conversion():
    """Test is hbjson is being converted into vtk polydata correctly."""
    file_path = r'tests/assets/gridbased.hbjson'
    model = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Mesh)

    assert len(model.shades.data) == 40
    assert len(model.doors.data) == 0
    assert len(model.apertures.data) == 7
    assert len(model.walls.data) == 8
    assert len(model.floors.data) == 2
    assert len(model.roof_ceilings.data) == 2
    assert len(model.air_boundaries.data) == 0
    assert len(model.sensor_grids.data) == 2


def test_default_colors():
    """Test default colors for the model objects."""
    file_path = r'tests/assets/revit_model/model.hbjson'
    model = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Mesh)

    assert model.get_default_color('Aperture') == Color(63, 179, 255, 127)
    assert model.get_default_color('Door') == Color(159, 149, 99, 255)
    assert model.get_default_color('Shade') == Color(119, 74, 189, 255)
    assert model.get_default_color('Wall') == Color(229, 179, 59, 255)
    assert model.get_default_color('Floor') == Color(255, 127, 127, 255)
    assert model.get_default_color('RoofCeiling') == Color(127, 19, 19, 255)
    assert model.get_default_color('AirBoundary') == Color(255, 255, 199, 255)
    assert model.get_default_color('Grid') == Color(235, 63, 102, 255)


def test_views():
    """Test if views are being read from hbjson."""
    file_path = r'tests/assets/viewbased.hbjson'
    model = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Mesh)
    assert len(model.cameras) == 1


def test_get_modeldataset():
    """Test get_modeldataset method."""
    file_path = r'tests/assets/gridbased.hbjson'
    model = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Mesh)

    assert model.get_modeldataset(DataSetNames.wall).name == 'Wall'
