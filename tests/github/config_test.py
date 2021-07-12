"""Unit tests for the config module."""


from _pytest.config import Config
import pytest

from pydantic import ValidationError
from honeybee_vtk.legend_parameter import LegendParameter, Orientation, ColorSets
from honeybee_vtk.model import Model
from honeybee_vtk.scene import Scene
from honeybee_vtk.camera import Camera
from honeybee_vtk.actor import Actor
from honeybee_vtk.config import Autocalculate, DataConfig, LegendConfig, _load_legend_parameters,\
    load_config, TextConfig, DecimalCount
from honeybee_vtk.vtkjs.schema import SensorGridOptions

file_path = r'tests/assets/gridbased.hbjson'
valid_json_path = r'tests/assets/config/valid.json'
range_json_path = r'tests/assets/config/range.json'
invalid_json_path = r'tests/assets/config/invalid.json'
more_grids = r'tests/assets/config/more_grids.json'
identifier_mismatch = r'tests/assets/config/identifier_mismatch.json'
short_length = r'tests/assets/config/short_length.json'


def test_text_config_defaults():
    text_config = TextConfig()
    assert text_config.color == [0, 0, 0]
    assert text_config.size == 30
    assert text_config.bold == False


def test_text_config_validators():
    text_config = TextConfig()

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

    data_config = DataConfig(
        identifier='Daylight-factor', object_type='grid', unit='Percentage',
        path='tests/assets/df_results')

    assert not data_config.hide
    assert data_config.legend_parameters == LegendConfig()


def test_data_config_validators():
    # all required fields missing
    with pytest.raises(KeyError):
        data_config = DataConfig()

    # required fields missing
    with pytest.raises(ValidationError):
        data_config = DataConfig(identifier='Starlight')

    # invalid folder path
    with pytest.raises(ValidationError):
        data_config = DataConfig(
            identifier='Daylight-factor', object_type='grid', unit='Percentage',
            folder_path='tests/assets/config/valid.json')

    # invalid object type
    with pytest.raises(ValidationError):
        data_config = DataConfig(
            identifier='Daylight-factor', object_type='ground', unit='Percentage',
            folder_path='tests/assets/df_results')


def test_data_config_legend_parameter_validator():
    # width greater than position in X direction
    legend_params = LegendConfig()
    legend_params.position = [0.5, 0.5]
    legend_params.width = 0.6
    with pytest.raises(ValidationError):
        data_config = DataConfig(
            identifier='Daylight-factor', object_type='grid', unit='Percentage',
            folder_path='tests/assets/df_results', legend_parameters=legend_params)

    # height greater than position in Y direction
    legend_params = LegendConfig()
    legend_params.position = [0.5, 0.5]
    legend_params.height = 0.6
    with pytest.raises(ValidationError):
        data_config = DataConfig(
            identifier='Daylight-factor', object_type='grid', unit='Percentage',
            folder_path='tests/assets/df_results', legend_parameters=legend_params)


def test_load_legend_parameter():

    model = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Mesh)
    cameras = model.cameras
    actors = Actor.from_model(model)
    scene = Scene()
    scene.add_cameras(cameras)
    scene.add_actors(actors)

    # warning when loading data that is requested to be kept hidden
    with pytest.warns(Warning):
        load_config(valid_json_path, model, scene)

    # warning when loading data without min and max of legend specified
    with pytest.warns(Warning):
        load_config(range_json_path, model, scene)


model = Model.from_hbjson(file_path)
scene = Scene()


def test_validate_data_invalid_json():
    with pytest.raises(TypeError):
        load_config(invalid_json_path, model, scene)


def test_validate_data_grids_not_loaded():
    with pytest.raises(AssertionError):
        load_config(valid_json_path, model, scene)


model_grids_loaded = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Mesh)
scene_grids_loaded = Scene()
cameras = model_grids_loaded.cameras
actors = Actor.from_model(model_grids_loaded)
scene_grids_loaded.add_cameras(cameras)
scene_grids_loaded.add_actors(actors)


def test_validate_data_number_of_grids_mismatch():
    with pytest.raises(AssertionError):
        load_config(more_grids, model_grids_loaded, scene_grids_loaded)


def test_validate_data_identifier_mismatch():
    with pytest.raises(AssertionError):
        load_config(identifier_mismatch, model_grids_loaded, scene_grids_loaded)


def test_validate_data_file_lengths_mismatch():
    with pytest.raises(ValueError):
        load_config(short_length, model_grids_loaded, scene_grids_loaded)
