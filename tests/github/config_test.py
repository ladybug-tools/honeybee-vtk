"""Unit tests for the config module."""


from honeybee_vtk.types import DataSetNames
from _pytest.config import Config
import pytest

from pydantic import ValidationError
from honeybee_vtk.legend_parameter import LegendParameter, Orientation, ColorSets
from honeybee_vtk.model import Model
from honeybee_vtk.scene import Scene
from honeybee_vtk.camera import Camera
from honeybee_vtk.actor import Actor
from honeybee_vtk.config import Autocalculate, DataConfig, LegendConfig,\
    _load_legend_parameters, load_config, TextConfig, DecimalCount, \
    _validate_simulation_data, _load_data, _get_grid_type, _get_legend_range
from honeybee_vtk.vtkjs.schema import DisplayMode, SensorGridOptions


def test_text_config_defaults():
    """Testting default settings of the TextConfig object."""
    text_config = TextConfig()
    assert text_config.color == [0, 0, 0]
    assert text_config.size == 0
    assert text_config.bold == False


def test_text_config_validators():
    """Testting validators of TextConfig object."""
    text_config = TextConfig()

    with pytest.raises(ValidationError):
        text_config.color = [0, 0, 266]

    with pytest.raises(ValidationError):
        text_config.color = [-1, 0, 255]

    with pytest.raises(ValidationError):
        text_config.size = -15

    with pytest.raises(ValidationError):
        text_config.color = 'Red'

    with pytest.raises(ValidationError):
        text_config.bold = "okay"

    text_config.bold = 1
    assert text_config.bold == True

    text_config.bold = 'no'
    assert text_config.bold == False


def test_legend_config_defaults():
    """Testting default settings of the LegendConfig object."""
    legend_config = LegendConfig()
    assert legend_config.color_set == ColorSets.ecotect
    assert legend_config.min == Autocalculate()
    assert legend_config.max == Autocalculate()
    assert not legend_config.hide_legend
    assert legend_config.orientation == Orientation.horizontal
    assert legend_config.width == 0.45
    assert legend_config.height == 0.05
    assert legend_config.position == [0.5, 0.1]
    assert legend_config.color_count == Autocalculate()
    assert legend_config.label_count == Autocalculate()
    assert legend_config.decimal_count == DecimalCount.default
    assert legend_config.preceding_labels == False
    assert legend_config.label_parameters == TextConfig()
    assert legend_config.title_parameters == TextConfig(bold=True)


def text_legend_config_validators():
    """Testting validators of LegendConfig object."""
    legend_config = LegendConfig()

    with pytest.raises(ValidationError):
        legend_config.colors = "red"

    with pytest.raises(ValidationError):
        legend_config.colors = 255

    legend_config.min = -10
    assert legend_config.min == -10

    with pytest.raises(ValidationError):
        legend_config.max = -20

    with pytest.raises(ValidationError):
        legend_config.min = 'less'

    with pytest.raises(ValidationError):
        legend_config.max = 'more'

    with pytest.raises(ValidationError):
        legend_config.orientation = 'up'

    with pytest.raises(ValidationError):
        legend_config.width = 200

    with pytest.raises(ValidationError):
        legend_config.height == 500

    with pytest.raises(ValidationError):
        legend_config.position = (0, 5, 4)

    with pytest.raises(ValidationError):
        legend_config.color_count = 25

    with pytest.raises(ValidationError):
        legend_config.label_count = 26

    with pytest.raises(ValidationError):
        legend_config.decimal_count = 2

    with pytest.raises(ValidationError):
        legend_config.preceding_labels = 'no'

    with pytest.raises(ValidationError):
        legend_config.label_parameters = {'color': [0, 0, 0]}

    with pytest.raises(ValidationError):
        legend_config.title_parameters = {'color': [0, 0, 0]}


def test_data_config_defaults():
    """Testing default settings of the DataConfig object."""
    data_config = DataConfig(
        identifier='Daylight-factor', object_type='grid', unit='Percentage',
        path='tests/assets/df_results')

    assert not data_config.hide
    assert data_config.legend_parameters == LegendConfig()


def test_data_config_validators():
    """Testing if correct errors are being raised."""

    # all required fields missing
    with pytest.raises(ValidationError):
        data_config = DataConfig()

    # required fields missing
    with pytest.raises(ValidationError):
        data_config = DataConfig(identifier='Starlight')

    # invalid object type
    with pytest.raises(ValidationError):
        data_config = DataConfig(
            identifier='Daylight-factor', object_type='ground', unit='Percentage',
            path='tests/assets/df_results')


def test_data_config_legend_parameter_validator():
    """Testing the legend parameter validator in DataConfig object."""

    # width greater than position in X direction
    legend_params = LegendConfig()
    legend_params.position = [0.5, 0.5]
    legend_params.width = 0.6
    with pytest.raises(ValidationError):
        data_config = DataConfig(
            identifier='Daylight-factor', object_type='grid', unit='Percentage',
            path='tests/assets/df_results', legend_parameters=legend_params)

    # height greater than position in Y direction
    legend_params = LegendConfig()
    legend_params.position = [0.5, 0.5]
    legend_params.height = 0.6
    with pytest.raises(ValidationError):
        data_config = DataConfig(
            identifier='Daylight-factor', object_type='grid', unit='Percentage',
            path='tests/assets/df_results', legend_parameters=legend_params)


def test_load_legend_parameter():
    """Testing load_legend_parameters function."""
    model_grid_mesh = r'tests/assets/gridbased.hbjson'
    valid_json_path = r'tests/assets/config/valid.json'

    model = Model.from_hbjson(model_grid_mesh, load_grids=SensorGridOptions.Mesh)
    cameras = model.cameras
    actors = Actor.from_model(model)
    scene = Scene()
    scene.add_cameras(cameras)
    scene.add_actors(actors)

    # warning when loading data that is requested to be kept hidden
    with pytest.warns(Warning):
        load_config(valid_json_path, model, scene, validation=True, legend=True)


def test_validate_data_invalid_json():
    """Tets if invalid json is detected."""
    model_grid_mesh = r'tests/assets/gridbased.hbjson'
    invalid_json_path = r'tests/assets/config/invalid.json'
    model = Model.from_hbjson(model_grid_mesh, load_grids=SensorGridOptions.Mesh)
    scene = Scene()
    with pytest.raises(TypeError):
        load_config(invalid_json_path, model, scene)


def test_validate_data_grids_not_loaded():
    model_grid_mesh = r'tests/assets/gridbased.hbjson'
    valid_json_path = r'tests/assets/config/valid.json'
    model = Model.from_hbjson(model_grid_mesh)
    scene = Scene()
    with pytest.raises(AssertionError):
        load_config(valid_json_path, model, scene)


def test_validate_data_number_of_grids_mismatch():
    model_grid_mesh = r'tests/assets/gridbased.hbjson'
    more_grids = r'tests/assets/config/more_grids.json'
    model_grids_loaded = Model.from_hbjson(
        model_grid_mesh, load_grids=SensorGridOptions.Mesh)
    scene_grids_loaded = Scene()
    cameras = model_grids_loaded.cameras
    actors = Actor.from_model(model_grids_loaded)
    scene_grids_loaded.add_cameras(cameras)
    scene_grids_loaded.add_actors(actors)

    with pytest.raises(AssertionError):
        load_config(more_grids, model_grids_loaded, scene_grids_loaded, validation=True)


def test_validate_data_identifier_mismatch():
    model_grid_mesh = r'tests/assets/gridbased.hbjson'
    identifier_mismatch = r'tests/assets/config/identifier_mismatch.json'
    model_grids_loaded = Model.from_hbjson(
        model_grid_mesh, load_grids=SensorGridOptions.Mesh)
    scene_grids_loaded = Scene()
    cameras = model_grids_loaded.cameras
    actors = Actor.from_model(model_grids_loaded)
    scene_grids_loaded.add_cameras(cameras)
    scene_grids_loaded.add_actors(actors)

    with pytest.raises(AssertionError):
        load_config(identifier_mismatch, model_grids_loaded,
                    scene_grids_loaded, validation=True)


def test_validate_data_file_lengths_mismatch():
    model_grid_mesh = r'tests/assets/gridbased.hbjson'
    short_length = r'tests/assets/config/short_length.json'
    model_grids_loaded = Model.from_hbjson(
        model_grid_mesh, load_grids=SensorGridOptions.Mesh)
    scene_grids_loaded = Scene()
    cameras = model_grids_loaded.cameras
    actors = Actor.from_model(model_grids_loaded)
    scene_grids_loaded.add_cameras(cameras)
    scene_grids_loaded.add_actors(actors)

    with pytest.raises(ValueError):
        load_config(short_length, model_grids_loaded, scene_grids_loaded)


def test_grid_display_mode():
    """Test if correct dosplay mode is being selected for grids based on the type of
    grids in the model."""
    model_grid_mesh = r'tests/assets/gridbased.hbjson'
    valid_json_path = r'tests/assets/config/valid.json'
    model_grids_loaded = Model.from_hbjson(
        model_grid_mesh, load_grids=SensorGridOptions.Mesh)
    scene_grids_loaded = Scene()
    cameras = model_grids_loaded.cameras
    actors = Actor.from_model(model_grids_loaded)
    scene_grids_loaded.add_cameras(cameras)
    scene_grids_loaded.add_actors(actors)

    model = load_config(valid_json_path, model_grids_loaded, scene_grids_loaded)
    assert model.sensor_grids.display_mode == DisplayMode.SurfaceWithEdges

    model_sensors_loaded = Model.from_hbjson(
        model_grid_mesh, load_grids=SensorGridOptions.Sensors)

    model = load_config(valid_json_path, model_sensors_loaded, scene_grids_loaded)
    assert model.sensor_grids.display_mode == DisplayMode.Points


def test_get_grid_type():
    """Test if _get_grid_type returns correct grid type."""
    model_grid_mesh = r'tests/assets/gridbased.hbjson'
    model_grids_loaded = Model.from_hbjson(
        model_grid_mesh, load_grids=SensorGridOptions.Mesh)
    assert _get_grid_type(model_grids_loaded) == 'meshes'

    model_sensors_loaded = Model.from_hbjson(
        model_grid_mesh, load_grids=SensorGridOptions.Sensors)
    assert _get_grid_type(model_sensors_loaded) == 'points'


def test_get_legend_range():
    """Test if the _get_legend_range supplies correct range."""
    # if neither min nor max is set
    lc = LegendConfig()
    dc = DataConfig(identifier='test', object_type=DataSetNames.grid,
                    unit='sample', path='.', legend_parameters=lc)
    legend_range = _get_legend_range(dc)
    assert legend_range == [None, None]

    # if both min and max are set
    lc = LegendConfig(min=0, max=0)
    dc = DataConfig(identifier='test', object_type=DataSetNames.grid,
                    unit='sample', path='.', legend_parameters=lc)
    legend_range = _get_legend_range(dc)
    assert legend_range == [0.0, 0.0]

    # if only min is set
    lc = LegendConfig(min=0)
    dc = DataConfig(identifier='test', object_type=DataSetNames.grid,
                    unit='sample', path='.', legend_parameters=lc)
    legend_range = _get_legend_range(dc)
    assert legend_range == [0.0, None]

    # if only max is set
    lc = LegendConfig(max=0)
    dc = DataConfig(identifier='test', object_type=DataSetNames.grid,
                    unit='sample', path='.', legend_parameters=lc)
    legend_range = _get_legend_range(dc)
    assert legend_range == [None, 0.0]
