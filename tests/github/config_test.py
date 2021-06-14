"""Unit tests for the config module."""
import pytest
from honeybee_vtk.model import Model
from honeybee_vtk.config import load_config
from honeybee_vtk.vtkjs.schema import SensorGridOptions


def test_config():
    """Test loading config file."""
    file_path = r'tests/assets/gridbased.hbjson'
    valid_json_path = r'tests/assets/config/valid.json'
    invalid_json_path = r'tests/assets/config/invalid.json'
    more_grids = r'tests/assets/config/more_grids.json'
    no_file = r'tests/assets/config/no_file.json'
    more_files = r'tests/assets/config/more_files.json'
    short_length = r'tests/assets/config/short_length.json'

    model = Model.from_hbjson(file_path)

    # invalid json file
    with pytest.raises(TypeError):
        load_config(invalid_json_path, model=model)

    # when grids are not loaded on a model and one is trying to mount data for grids
    print(valid_json_path, model)
    with pytest.raises(AssertionError):
        load_config(json_path=valid_json_path, model=model)

    model = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Mesh)

    # trying to load more grids than grids in the model
    with pytest.raises(ValueError):
        load_config(more_grids, model)

    # Empty list if provided in file_paths
    with pytest.raises(ValueError):
        load_config(no_file, model)

    # If more than one files are provided in file_path for non-grid object_type
    with pytest.raises(ValueError):
        load_config(more_files, model)

    # if file lengths do not match grid size
    with pytest.raises(ValueError):
        load_config(short_length, model)
