"""Unit tests for data module."""

import pytest
from pydantic import ValidationError
from honeybee_vtk.model import Model
from honeybee_vtk.data import check_data_config
from honeybee_vtk.vtkjs.schema import SensorGridOptions


file_path = r'./tests/assets/gridbased.hbjson'
model = Model.from_hbjson(hbjson=file_path, load_grids=SensorGridOptions.Mesh)


def test_invalid_path():
    """Test whether invalid path of json raises an error."""
    invalid_json_path = r'./tests/assets/config/valids.json'

    with pytest.raises(FileExistsError):
        config = check_data_config(invalid_json_path, model)


def test_invalid_json():
    """Test whether error is raised for an invalid json."""
    invalid_config = r'./tests/assets/config/invalid.json'

    with pytest.raises(TypeError):
        config = check_data_config(invalid_config, model)


def test_valid_json():
    """Test if data for the grid can be assessed successfully."""
    valid_config = r'./tests/assets/config/valid.json'
    config = check_data_config(valid_config, model)
    assert isinstance(config, dict)
