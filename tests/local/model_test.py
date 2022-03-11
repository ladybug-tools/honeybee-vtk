"""Unit tests for the model module."""

import os
import shutil
import pytest
from honeybee_vtk.model import Model
from honeybee_vtk.vtkjs.schema import SensorGridOptions


def test_grid_to_images():
    """Test if grids are being converted to images."""
    file_path = r'tests/assets/gridbased.hbjson'
    json_path = r'tests/assets/config/valid.json'
    model = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Mesh)

    # create a folder to store the images
    target_folder = r'tests/assets/temp'
    if os.path.isdir(target_folder):
        shutil.rmtree(target_folder)
    os.mkdir(target_folder)

    file_names = ['Daylight-Factor_TestRoom_1.png', 'Daylight-Factor_TestRoom_2.png',
                  'UDI_TestRoom_1.png', 'UDI_TestRoom_2.png', ]
    model.to_grid_images(config=json_path, folder=target_folder)
    for file in os.listdir(target_folder):
        assert file in file_names

    shutil.rmtree(target_folder)


def test_grid_to_images():
    """Test if grids selected grids are being exported."""
    file_path = r'tests/assets/gridbased.hbjson'
    json_path = r'tests/assets/config/valid.json'
    model = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Mesh)

    # create a folder to store the images
    target_folder = r'tests/assets/temp'
    if os.path.isdir(target_folder):
        shutil.rmtree(target_folder)
    os.mkdir(target_folder)

    file_names = ['Daylight-Factor_TestRoom_1.png', 'UDI_TestRoom_1.png']
    model.to_grid_images(config=json_path, folder=target_folder,
                         grid_filter=['TestRoom_1'])
    for file in os.listdir(target_folder):
        assert file in file_names

    shutil.rmtree(target_folder)


def test_grid_to_images_assertion_error():
    """Test if AssertionError is raised when grids are not loaded."""
    file_path = r'tests/assets/gridbased.hbjson'
    json_path = r'tests/assets/config/valid.json'
    model = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Ignore)

    target_folder = r'tests/assets/temp'
    if os.path.isdir(target_folder):
        shutil.rmtree(target_folder)
    os.mkdir(target_folder)

    with pytest.raises(AssertionError):
        model.to_grid_images(config=json_path, folder=target_folder)

    shutil.rmtree(target_folder)


def test_grid_to_images_value_error():
    """Test if valueerror is raised on wrong grid identifier."""
    file_path = r'tests/assets/gridbased.hbjson'
    json_path = r'tests/assets/config/valid.json'
    model = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Mesh)

    target_folder = r'tests/assets/temp'
    if os.path.isdir(target_folder):
        shutil.rmtree(target_folder)
    os.mkdir(target_folder)

    with pytest.raises(ValueError):
        model.to_grid_images(config=json_path, folder=target_folder,
                             grid_filter=['abc'],)

    shutil.rmtree(target_folder)
