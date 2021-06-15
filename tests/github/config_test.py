"""Unit tests for the config module."""

import pydantic
import pytest
from pydantic import ValidationError
from honeybee_vtk.model import Model
from honeybee_vtk.scene import Scene
from honeybee_vtk.config import load_config
from honeybee_vtk.vtkjs.schema import SensorGridOptions


def test_data_config():
    """Test loading config file."""

    file_path = r'tests/assets/gridbased.hbjson'
    valid_json_path = r'tests/assets/config/valid.json'
    invalid_json_path = r'tests/assets/config/invalid.json'
    more_grids = r'tests/assets/config/more_grids.json'
    no_file = r'tests/assets/config/no_file.json'
    more_files = r'tests/assets/config/more_files.json'
    short_length = r'tests/assets/config/short_length.json'
    invalid_object_type = r'tests/assets/config/invalid_object_type.json'
    invalid_file_paths = r'tests/assets/config/invalid_file_paths.json'

    model = Model.from_hbjson(file_path)
    scene = Scene()

    # invalid json file
    with pytest.raises(TypeError):
        load_config(invalid_json_path, model, scene)

    # when grids are not loaded on a model and one is trying to mount data for grids
    with pytest.raises(AssertionError):
        load_config(valid_json_path, model, scene)

    model = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Mesh)

    # trying to load more grids than grids in the model
    with pytest.raises(ValueError):
        load_config(more_grids, model, scene)

    # if Empty list is provided in file_paths
    with pytest.raises(ValueError):
        load_config(no_file, model, scene)

    # If more than one files are provided in file_path for non-grid object_type
    with pytest.raises(ValueError):
        load_config(more_files, model, scene)

    # if file lengths do not match grid size
    with pytest.raises(ValueError):
        load_config(short_length, model, scene)

    # invalid object_type value
    with pytest.raises(ValidationError):
        load_config(invalid_object_type, model, scene)

    # invalid file paths
    with pytest.raises(ValidationError):
        load_config(invalid_file_paths, model, scene)


def test_legend_config():
    """Test adding legend parameters."""

    file_path = r'tests/assets/gridbased.hbjson'
    invalid_colors = r'tests/assets/config/invalid_colors.json'
    invalid_orientation = r'tests/assets/config/invalid_orientation.json'
    invalid_label_format = r'tests/assets/config/invalid_label_format.json'
    color_by = r'tests/assets/config/color_by.json'

    model = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Mesh)
    scene = Scene()

    # if invalid colors in legend parameters raises error
    with pytest.raises(ValidationError):
        load_config(invalid_colors, model, scene)

    # if invalid orientation in legend parameters raises error
    with pytest.raises(ValidationError):
        load_config(invalid_orientation, model, scene)

    # if invalid Label_format in legend parameters raises error
    with pytest.raises(ValidationError):
        load_config(invalid_label_format, model, scene)

    # if warning is raised in case legend parameters are provided for data that is
    # not going to color the object_type
    with pytest.warns(Warning):
        load_config(color_by, model, scene)
