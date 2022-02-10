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

    # convert all the grids to images
    model.to_grid_images(json_path, folder=target_folder)
    for count, file in enumerate(os.listdir(target_folder)):
        assert file == f'Daylight-Factor_TestRoom_{count+1}.png'

    # remove the folder
    shutil.rmtree(target_folder)


def test_grid_to_images_assertion_error():
    """Test if grids are being converted to images."""
    file_path = r'tests/assets/gridbased.hbjson'
    json_path = r'tests/assets/config/valid.json'
    model = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Ignore)

    # create a folder to store the images
    target_folder = r'tests/assets/temp'
    if os.path.isdir(target_folder):
        shutil.rmtree(target_folder)
    os.mkdir(target_folder)

    # Make sure the assertion error is raised when this method is used on a model
    # that does not have grids loaded.
    with pytest.raises(AssertionError):
        model.to_grid_images(json_path, folder=target_folder)

    # remove the folder
    shutil.rmtree(target_folder)


def test_grid_to_images_value_error():
    """Test if grids are being converted to images."""
    file_path = r'tests/assets/gridbased.hbjson'
    json_path = r'tests/assets/config/valid_with_invalid_grid_filter.json'
    model = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Mesh)

    # create a folder to store the images
    target_folder = r'tests/assets/temp'
    if os.path.isdir(target_folder):
        shutil.rmtree(target_folder)
    os.mkdir(target_folder)

    # Make sure the assertion error is raised when this method is used on a model
    # that does not have grids loaded.
    with pytest.raises(ValueError):
        model.to_grid_images(json_path, folder=target_folder)

    # remove the folder
    shutil.rmtree(target_folder)
