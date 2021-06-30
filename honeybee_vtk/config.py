"""Data json schema and validation."""

from __future__ import annotations
import json
import pathlib
import warnings

from typing import List, Union
from pydantic import BaseModel, validator, Field, constr
from .types import DataSetNames
from .legend_parameter import Colors, Font, LabelFormat, Orientation
from .model import Model
from ._helper import get_line_count, get_min_max
from .vtkjs.schema import DisplayMode
from .scene import Scene


class FontConfig(BaseModel):
    """Config for the fonts to be used in a legend."""

    color: List[int] = Field(
        [0, 0, 0],
        description='An array of three integer values representing R, G, and B values'
        ' for the color of fonts.'
    )

    size: int = Field(
        30,
        description='Size of fonts in points.'
    )

    bold: bool = Field(
        False,
        description='Bool value to indicate whether to make the fonts bold or not.'
    )


class LegendConfig(BaseModel):
    """Config for the legend to be created from a dataset."""

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

    position: List[float] = Field(
        [0.5, 0.1],
        description='A tuple of two decimal values. The values represent the fraction'
        ' of viewport width and the fraction of viewport height.'
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

    color_count: int = Field(
        0,
        description='An integer representing the number of colors in a legend.'
    )

    label_count: int = Field(
        0,
        description='An integer representing the number of text labels on a legend.'
    )

    label_format: str = Field(
        'integer',
        description='Format of legend labels.'
    )

    label_position: int = Field(
        0,
        description='0 or 1 to decide whether the legend title and the legend labels'
        ' will precede the legend or not.'
    )

    label_fonts: FontConfig = Field(
        FontConfig(),
        description='Font parameters for the fonts to be used for the labels on the'
        ' legend.'
    )

    title_fonts: FontConfig = Field(
        FontConfig(bold=True),
        description='Font parameters for the fonts to be used in the title of the'
        ' legend.'
    )

    @validator('color_set')
    def validate_color_set(cls, v: str) -> str:
        try:
            return Colors[v]
        except KeyError:
            raise KeyError(
                f'color_set must be from {tuple(dir(Colors)[4:])}. Instead go {v}.'
            )

    @validator('min')
    def validate_min(cls, v: float) -> float:
        print("this is v", v)
        if not isinstance(v, (float, int)):
            raise ValueError('Min value has to be a float or an integer.')
        return v

    @validator('max')
    def validate_max(cls, v: float, values) -> float:
        print(values)
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

    @validator('label_format')
    def validate_label_format(cls, v: str) -> str:
        label_formats = dir(LabelFormat)[4:]
        if v in label_formats:
            return v
        else:
            raise ValueError(
                f'Label format must be from {label_formats}. Instead got {v}.'
            )


class DataConfig(BaseModel):
    """Config for each dataset you'd like to load on a honeybee-vtk model."""

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

    file_paths: List[str] = Field(
        description='List of paths to the file or files that you are trying to use as'
        ' data.'
    )

    color_by: bool = Field(
        False,
        description='Bool value to indicate if this data should be used to color the'
        ' object type in the model.'
    )

    legend_parameters: LegendConfig = Field(
        LegendConfig(),
        description='Legend parameters to create legend out of the this dataset.'
    )

    @validator('object_type')
    def validate_object(cls, v: str) -> str:
        if v in DataSetNames:
            return v
        else:
            raise ValueError(
                f'Object name should be from these {tuple(dir(DataSetNames)[4:])}.'
                f' Instead got {v}.'
            )

    @validator('file_paths')
    def validate_paths(cls, v: List[str]) -> List[str]:
        if all([pathlib.Path(path).is_file() for path in v]):
            return v
        else:
            paths = tuple([path for path in v if not pathlib.Path(path).is_file()])
            raise ValueError(
                f'Following file paths are not valid {paths}.'
            )


def _validate_data(data: DataConfig, model: Model) -> bool:
    """Cross check data with model.

    For grids, it will be checked if the number of data files and the names of the
    data files match with the grid identifiers. For other than grid objects, it will
    be checked that only one data file is provided and the length of the data file
    matches the length of Polydata in the model. This is a helper method to the
    public load_config method.

    Args:
        data: A DataConfig object.
        model: A honeybee-vtk model.

    Returns:
        A boolean value.
    """
    print('\n', data, '\n')

    # if file_paths is empty
    if not data.file_paths:
        raise ValueError(
            f'For object with name {data.name} There are not file paths'
            ' provided to load data from.'
        )

    # if object name is "grid" check that the name of files match the grid names
    if data.object_type == DataSetNames.grid:
        # make sure grids are loaded on the model if grid data is to be mounted
        assert len(model.sensor_grids.data) > 0, 'Sensor grids are not loaded on'\
            ' this model. Reload them using grid options.'

        grid_names = [grid.identifier for grid in model.sensor_grids.data]
        file_names = [pathlib.Path(path).stem for path in data.file_paths]
        names_in_grids = all([name in grid_names for name in file_names])

        # the number of data files must not exceed the number of grids
        if len(file_names) > len(grid_names):
            raise ValueError(
                f'There are only {len(grid_names)} grids in the model and the'
                f' identifiers of those grids are {tuple(grid_names)}.'
            )

        # TODO: remove this check in the next iteration
        # make sure there's one file for each grid in the model
        if not names_in_grids:
            raise ValueError(
                'Make sure the file names match the grid identifiers. The'
                f' identifiers of the grids in the model are {tuple(grid_names)}.'
            )

        # make sure length of each file matches the number of sensors in grid
        file_lengths = [get_line_count(file_path) for file_path in data.file_paths]
        num_sensors = [polydata.GetNumberOfCells()
                       for polydata in model.sensor_grids.data]

        if file_lengths != num_sensors:
            path_matches = {
                data.file_paths[i]: file_lengths[i] == num_sensors[i] for i in
                range(len(data.file_paths))
            }
            paths_to_report = [
                path for path in path_matches if path_matches[path] is False]
            raise ValueError(
                'File lengths must match grid sizes. Lengths of'
                f' following files do not match grid size {tuple(paths_to_report)}.')

        return True

    # if object_name is other than grid check that length of data matches the length
    # of data in the model for that object.
    elif isinstance(data.object_type, DataSetNames):

        # only one file is accepted
        if len(data.file_paths) > 1:
            raise ValueError(
                'Only one file path needs to be provided in order to load data on'
                f' {data.object_type}. Multiple files are provided in the config'
                ' file.'
            )

        # match length of file with the number of faces in the model
        if get_line_count(data.file_paths[0]) != len(
                model.get_modeldataset(data.object_type).data):
            raise ValueError(
                'The length of data in the file does not match the number of'
                f' {data.object_type} objects in the model.'
            )
        return True

    else:
        raise ValueError(
            ' object_name must be from one of these'
            f' {tuple(dir(DataSetNames)[4:])}. Instead got {data.object_type}.'
        )


def _load_data(data: DataConfig, model: Model) -> None:
    """Load validate data on a honeybee-vtk model.

    This is a helper method to the public load_config method.

    Args:
        data: A DataConfig object.
        model: A honeybee-vtk model.
    """
    # if data is for a ModelDataSet grid
    if data.object_type == DataSetNames.grid:

        result = []
        for file_path in data.file_paths:
            res_file = pathlib.Path(file_path)
            grid_res = [float(v)
                        for v in res_file.read_text().splitlines()]
            result.append(grid_res)

    # if data is for a ModelDataSet other than grid
    elif isinstance(data.object_type, DataSetNames):
        res_file = pathlib.Path(data.file_paths[0])
        result = [[float(v)] for v in res_file.read_text().splitlines()]

    ds = model.get_modeldataset(data.object_type)
    ds.add_data_fields(
        result, name=data.identifier, data_range=get_min_max(result))
    if data.color_by:
        ds.color_by = data.identifier
    ds.display_mode = DisplayMode.SurfaceWithEdges


def _load_legend_parameters(data: DataConfig, model: Model, scene: Scene) -> None:
    """Load legend_parameters.

    Args:
        data: A Dataconfig object.
        model: A honeybee-vtk model object.
        scene: A honeyebee-vtk scene object.
    """
    if data.legend_parameters and data.color_by:

        legend_params = data.legend_parameters
        legend = scene.legend_parameter(data.identifier)

        if legend_params.color_set:
            legend.colors = legend_params.color_set

        legend.unit = data.unit

        # assign legend range
        range = (legend_params.min, legend_params.max)
        if range[0] != 0 and range[1] != 0:
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
            legend.number_of_colors = legend_params.color_count
        else:
            legend.number_of_colors = None

        if legend_params.label_count > 0:
            legend.number_of_labels = legend_params.label_count
        else:
            legend.number_of_labels = None

        if legend_params.label_format:
            legend.label_format = LabelFormat[legend_params.label_format]

        legend.label_position = legend_params.label_position

        if legend_params.label_fonts:
            label_fonts = legend_params.label_fonts
            legend.label_font = Font(
                label_fonts.color, label_fonts.size, label_fonts.bold)

        if legend_params.title_fonts:
            title_fonts = legend_params.title_fonts
            legend.title_font = Font(
                title_fonts.color, title_fonts.size, title_fonts.bold)

    elif data.legend_parameters and not data.color_by:
        warnings.warn(
            f'Since {data.object_type} is not going to be colored by {data.identifier},'
            ' legend parameters will be ignored.'
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
