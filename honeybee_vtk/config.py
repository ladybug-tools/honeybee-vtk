"""Data json schema and validation."""

from __future__ import annotations
import json
import pathlib
import warnings

from typing import List
from pydantic import BaseModel, validator, Field
from .types import DataSetNames
from .legend_parameter import Colors, Text, DecimalCount, Orientation
from .model import Model
from ._helper import get_line_count, get_min_max
from .vtkjs.schema import DisplayMode
from .scene import Scene


class TextConfig(BaseModel):
    """Config for the text to be used in a legend.

    This object applies to text for legend title and legend labels as well.
    """

    class Config:
        validate_all = True
        validate_assignment = True

    color: List[int] = Field(
        [0, 0, 0],
        description='An array of three integer values representing R, G, and B values'
        ' for the color of text. Values from 0 to 255 are accepted.'
    )

    size: int = Field(
        30,
        description='Size of fonts in points.'
    )

    bold: bool = Field(
        False,
        description='Bool value to indicate whether to make the fonts bold or not.'
    )

    @validator('size')
    def negative_size_not_allowed(cls, v: int) -> int:
        if v < 0:
            raise ValueError('Text size cannot be a negative number.')
        return v


class LegendConfig(BaseModel):
    """Config for the legend to be created from a dataset."""
    class Config:
        validate_all = True
        validate_assignment = True

    color_set: str = Field(
        'ecotect',
        description='Color set to be used on data and legend. Currently, this field'
        ' only uses Ladybug color sets.'
    )

    min: float = Field(
        0.0,
        description='Minimum value for the legend. Also known as the lower end of the'
        ' legend. If min and max values are not specified autocalculated min and max'
        ' values will be used from data..'
    )

    max: float = Field(
        0.0,
        description='Maximum value for the legend. Also known as the higher end of the'
        ' legend. If min and max values are not specified autocalculated min and max'
        ' values will be used from data.'
    )

    show_legend: bool = Field(
        True,
        description='A bool value to indicate whether to show legend in the exported'
        ' images or not.'
    )

    orientation: Orientation = Field(
        Orientation.horizontal,
        description='Choose between horizontal and vertical orientation of legend.'
    )

    width: float = Field(
        0.45,
        description=' A decimal number representing the fraction of viewport width'
        ' that will be used to define the width of the legend.'
    )

    height: float = Field(
        0.05,
        description='A decimal number representing the fraction of viewport height'
        'that will be used to define the height of the legend.'
    )

    position: List[float] = Field(
        [0.5, 0.1],
        description='A tuple of two decimal values. The values represent the fraction'
        ' of viewport width and the fraction of viewport height.'
    )

    color_count: int = Field(
        0,
        description='An integer representing the number of colors in a legend.'
    )

    label_count: int = Field(
        0,
        description='An integer representing the number of text labels on a legend.'
    )

    decimal_count: str = Field(
        'default',
        description='Controlling the number of decimals on each label of the legend.'
    )

    preceding_labels: bool = Field(
        False,
        description='Boolean value to decide whether the legend title and the'
        ' legend labels will precede the legend or not.'
    )

    label_parameters: TextConfig = Field(
        TextConfig(),
        description='Text parameters for the labels on the legend.'
    )

    title_parameters: TextConfig = Field(
        TextConfig(bold=True),
        description='Text parameters for the title of the legend.'
    )

    @validator('color_set')
    def validate_color_set(cls, v: str) -> Colors:
        try:
            return Colors[v]
        except KeyError:
            raise KeyError(
                f'color_set must be from {tuple(dir(Colors)[4:])}. Instead go {v}.'
            )

    @validator('min')
    def validate_min(cls, v: float) -> float:
        if not isinstance(v, (float, int)):
            raise ValueError('Min value has to be a float or an integer.')
        return v

    @validator('max')
    def validate_max(cls, v: float, values) -> float:
        try:
            if v < values['min']:
                raise ValueError('Max value cannot be less than Min.')
        except KeyError:
            raise ValueError(
                'Min value is not valid. It has to be either an integer or a float.'
            )
        return v

    @validator('label_count')
    def label_count_equals_color_count(cls, v: int, values) -> int:
        num_colors = values['color_count']
        if v <= num_colors:
            return v
        else:
            raise ValueError(
                f'Label count, {v} cannot be greater than color count {num_colors}.')

    @validator('decimal_count')
    def validate_decimal_count(cls, v: str, values) -> DecimalCount:
        try:
            return DecimalCount[v]
        except KeyError:
            raise KeyError(
                f'Decimal count must be from {tuple(dir(DecimalCount)[4:])}. Instead got {v}.'
            )


class DataConfig(BaseModel):
    """Config for simulation results you'd like to load on a honeybee-vtk model."""

    class Config:
        validate_all = True
        validate_assignment = True

    identifier: str = Field(
        description='identifier to be given to data. Example, "Daylight-Factor".'
        ' This identifier needs to be unique in each of the DataConfig objects'
        ' one introduces using a config file. Having multiple DataConfig objects with'
        ' same modifier will raise an error.'
    )

    object_type: DataSetNames = Field(
        description='The name of the model object on which you would like to map this'
        ' data.'
    )

    unit: str = Field(
        description=' The unit of the data being loaded.'
    )

    folder_path: str = Field(
        description='Valid path to the folder with result files and the json file that'
        ' catalogues the results.'
    )

    hide: bool = Field(
        False,
        description='Boolean value to indicate if this data should be visible in the'
        ' exported images or not.'
    )

    legend_parameters: LegendConfig = Field(
        LegendConfig(identifier=identifier),
        description='Legend parameters to create legend out of the this dataset.'
    )

    @validator('folder_path')
    def validate_folder_path(cls, v: str) -> str:
        if pathlib.Path(v).is_dir():
            return v
        else:
            raise ValueError(
                'Not a valid folder path.'
            )

    @validator('legend_parameters')
    def check_pos_against_width_height(cls, v: LegendConfig, values) -> LegendConfig:
        id = values['identifier']
        if v.width >= 0.5 and v.position[0] >= 0.5 and v.width > v.position[0]:
            raise ValueError(
                f'Width of legend {id}, {v.width}'
                f' cannot be greater than the position of legend in X direction'
                f' {v.position[0]}.'
                ' Either update the position in X direction or update the'
                ' width of the legend.'
            )
        if v.height >= 0.5 and v.position[1] >= 0.5 and v.height > v.position[1]:
            raise ValueError(
                f'Height of legend {id}, {v.height}'
                f' cannot be greater than the position of legend in Y direction'
                f' {v.position[1]}.'
                ' Either update the position in Y direction or update the'
                ' height of the legend.'
            )
        return v


def _validate_data(data: DataConfig, model: Model) -> bool:
    """Match result data with the sensor grids in the model.

    It will be checked if the number of data files and the names of the
    data files match with the grid identifiers. This function does not support validating
    result data for other than sensor grids as of now.

    Args:
        data: A DataConfig object.
        model: A honeybee-vtk model.

    Returns:
        A boolean value.
    """
    grids_info_json = pathlib.Path(data.folder_path).joinpath('grids_info.json')
    # TODO: Confirm with Chris if this check for json is needed. I think it's not.
    try:
        with open(grids_info_json) as fh:
            grids_info = json.load(fh)
    except json.decoder.JSONDecodeError:
        raise TypeError(
            'grids_info is not a valid json file.'
        )
    else:
        assert len(model.sensor_grids.data) > 0, 'Sensor grids are not loaded on'\
            ' this model. Reload them using grid options.'
        # TODO: Make sure to remove this limitation. A user should not have to always
        # TODO: load all the grids
        assert len(model.sensor_grids.data) == len(grids_info), 'The number of result'\
            f' files {len(grids_info)} does for {data.identifier} does not match'\
            f' the number of sensor grids in the model {len(model.sensor_grids.data)}.'

        grids_model_identifiers = [grid.identifier for grid in model.sensor_grids.data]
        grids_info_identifiers = [grid['identifier'] for grid in grids_info]
        assert grids_model_identifiers == grids_info_identifiers, 'The identifiers of'\
            ' the sensor grids in the model do not match the identifiers of the grids'\
            f' in the grids_info.json for {data.identifier}.'

        # make sure length of each file matches the number of sensors in grid
        file_lengths = [grid['count'] for grid in grids_info]
        num_sensors = [polydata.GetNumberOfCells()
                       for polydata in model.sensor_grids.data]

        if file_lengths != num_sensors:
            length_matching = {
                grids_info_identifiers[i]: file_lengths[i] == num_sensors[i] for i in
                range(len(grids_model_identifiers))
            }
            names_to_report = [
                id for id in length_matching if length_matching[id] is False]
            raise ValueError(
                'File lengths of result files must match the number of sensors on grids.'
                ' Lengths of files with following names do not match'
                f' {tuple(names_to_report)}.')

        return True


def _load_data(data: DataConfig, model: Model) -> None:
    """Load validated data on a honeybee-vtk model.

    This is a helper method to the public load_config method.

    Args:
        data: A DataConfig object.
        model: A honeybee-vtk model.
    """
    # file paths to the result files
    file_paths = [result for result in pathlib.Path(
        data.folder_path).iterdir() if result.suffix != '.json']

    result = []
    for file_path in file_paths:
        res_file = pathlib.Path(file_path)
        grid_res = [float(v)
                    for v in res_file.read_text().splitlines()]
        result.append(grid_res)

    ds = model.get_modeldataset(data.object_type)
    ds.add_data_fields(
        result, name=data.identifier)
    if not data.hide:
        ds.color_by = data.identifier
    ds.display_mode = DisplayMode.SurfaceWithEdges


def _load_legend_parameters(data: DataConfig, model: Model, scene: Scene) -> None:
    """Load legend_parameters.

    Args:
        data: A Dataconfig object.
        model: A honeybee-vtk model object.
        scene: A honeyebee-vtk scene object.
    """
    if data.legend_parameters and not data.hide:

        legend_params = data.legend_parameters
        legend = scene.legend_parameter(data.identifier)

        legend.colors = legend_params.color_set
        legend.unit = data.unit

        # assign legend range
        range = (legend_params.min, legend_params.max)
        if range[1] != 0:
            legend.range = range
        else:
            print(f'For {data.identifier}, min and max values for the legend will be'
                  ' calculated automatically based on data.')

        legend.show_legend = legend_params.show_legend
        legend.orientation = legend_params.orientation
        legend.position = legend_params.position
        legend.width = legend_params.width
        legend.height = legend_params.height

        if legend_params.color_count > 0:
            legend.color_count = legend_params.color_count
        else:
            legend.color_count = None

        if legend_params.label_count > 0:
            legend.label_count = legend_params.label_count
        else:
            legend.label_count = None

        legend.decimal_count = legend_params.decimal_count
        legend.preceding_labels = legend_params.preceding_labels

        label_params = legend_params.label_parameters
        legend.label_parameters = Text(
            label_params.color, label_params.size, label_params.bold)

        title_params = legend_params.title_parameters
        legend.title_parameters = Text(
            title_params.color, title_params.size, title_params.bold)

    elif data.legend_parameters and data.hide:
        warnings.warn(
            f'Since {data.object_type.value.capitalize()} is not going to be'
            f' colored by {data.identifier}, legend parameters will be ignored.'
        )


def load_config(json_path: str, model: Model, scene: Scene) -> None:
    """Mount data on model from config json.

    Args:
        json_path: File path to the config json file.
        model: A honeybee-vtk model object.
        scene: A honeybee-vtk scene object.
    """
    # Check if json is valid
    try:
        with open(json_path) as fh:
            config = json.load(fh)
    except json.decoder.JSONDecodeError:
        raise TypeError(
            'Not a valid json file.'
        )
    else:
        for json_obj in config.values():
            data = DataConfig.parse_obj(json_obj)
            if _validate_data(data, model):
                _load_data(data, model)
                _load_legend_parameters(data, model, scene)
