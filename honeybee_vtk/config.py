"""Data json schema and validation."""

from __future__ import annotations
import json
import pathlib
import warnings

from typing import List, Union
from pydantic import BaseModel, validator, Field, constr, conint
from pydantic.types import confloat, conlist
from .types import DataSetNames
from .legend_parameter import ColorSets, Text, DecimalCount, Orientation
from .model import Model
from ._helper import get_line_count, get_min_max
from .vtkjs.schema import DisplayMode
from .scene import Scene


class Autocalculate(BaseModel):

    type: constr(regex='^Autocalculate$') = 'Autocalculate'


class TextConfig(BaseModel):
    """Config for the text to be used in a legend.

    This object applies to text for legend title and legend labels as well.
    """

    class Config:
        validate_all = True
        validate_assignment = True

    color: List[conint(ge=0, le=255)] = Field(
        [0, 0, 0],
        description='An array of three integer values representing R, G, and B values'
        ' for the color of text. Values from 0 to 255 are accepted.'
    )

    size: conint(ge=0) = Field(
        30,
        description='Text size in points.'
    )

    bold: bool = Field(
        False,
        description='Boolean value to indicate whether to make the text bold or not.'
    )


class LegendConfig(BaseModel):
    """Config for the legend to be created from a dataset."""
    class Config:
        validate_all = True
        validate_assignment = True

    color_set: ColorSets = Field(
        ColorSets.ecotect,
        description='Color set to be used on data and legend. Currently, this field'
        ' only uses Ladybug color sets. Defaults to using ecotect colorset.'
    )

    min: Union[Autocalculate, float] = Field(
        Autocalculate(),
        description='Minimum value for the legend. Also known as the lower end of the'
        ' legend. If min and max values are not specified, autocalculated min and max'
        ' values will be used from data.'
    )

    max: Union[Autocalculate, float] = Field(
        Autocalculate(),
        description='Maximum value for the legend. Also known as the higher end of the'
        ' legend. If min and max values are not specified, autocalculated min and max'
        ' values will be used from data.'
    )

    hide_legend: bool = Field(
        False,
        description='A bool value to indicate whether to show legend in the exported'
        ' images or not.'
    )

    orientation: Orientation = Field(
        Orientation.horizontal,
        description='Choose between horizontal and vertical orientation of legend.'
    )

    width: confloat(ge=0.05, le=0.95) = Field(
        0.45,
        description=' A decimal number representing the fraction of viewport width'
        ' that will be used to define the width of the legend.'
    )

    height: confloat(ge=0.05, le=0.95) = Field(
        0.05,
        description='A decimal number representing the fraction of viewport height'
        'that will be used to define the height of the legend.'
    )

    position: conlist(confloat(ge=0.05, le=0.95), min_items=2, max_items=2) = Field(
        [0.5, 0.1],
        description='A tuple of two decimal values. The values represent the fraction'
        ' of viewport width and the fraction of viewport height.'
    )

    color_count: Union[Autocalculate, int] = Field(
        Autocalculate(),
        description='An integer representing the number of colors in a legend. If not'
        ' specified, it defaults to the number of colors in a Ladybug color set.'
    )

    label_count: Union[Autocalculate, int] = Field(
        Autocalculate(),
        description='An integer representing the number of text labels on a legend.'
        ' Label count will have to be less than or equal to color count. It defaults'
        ' to vtk scalarbar default setting.'
    )

    decimal_count: DecimalCount = Field(
        DecimalCount.default,
        description='Controlling the number of decimals on each label of the legend.'
        'Accepted values are "default", "integer", "decimal_two", and "decimal_three".'
        'Defaults to VTKs default settings.'
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

    path: str = Field(
        description='Valid path to the folder with result files and the json file that'
        ' catalogues the results.'
    )

    hide: bool = Field(
        False,
        description='Boolean value to indicate if this data should be visible in the'
        ' exported images or not.'
    )

    legend_parameters: LegendConfig = Field(
        LegendConfig(),
        description='Legend parameters to create legend out of the this dataset.'
    )

    @validator('path')
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
    result data for other than sensor grids as of now. This is a helper method to the
    public load_config method.

    Args:
        data: A DataConfig object.
        model: A honeybee-vtk model.

    Returns:
        A boolean value.
    """
    grids_info_json = pathlib.Path(data.path).joinpath('grids_info.json')

    with open(grids_info_json) as fh:
        grids_info = json.load(fh)

    assert len(model.sensor_grids.data) > 0, 'Sensor grids are not loaded on'\
        ' this model. Reload them using grid options.'
    # TODO: Make sure to remove this limitation. A user should not have to always
    # TODO: load all the grids
    assert len(model.sensor_grids.data) == len(grids_info), 'The number of result'\
        f' files {len(grids_info)} does for {data.identifier} does not match'\
        f' the number of sensor grids in the model {len(model.sensor_grids.data)}.'

    grids_model_identifiers = [grid.identifier for grid in model.sensor_grids.data]
    grids_info_identifiers = [grid['full_id'] for grid in grids_info]
    assert grids_model_identifiers == grids_info_identifiers, 'The identifiers of'\
        ' the sensor grids in the model do not match the identifiers of the grids'\
        f' in the grids_info.json for {data.identifier}.'

    # make sure length of each file matches the number of sensors in grid
    file_lengths = [grid['count'] for grid in grids_info]

    # check if the grid data is meshes or points
    # if grid is sensors
    if model.sensor_grids.data[0].GetNumberOfCells() == 1 and \
            model.sensor_grids.data[0].GetNumberOfPoints() == file_lengths[0]:
        num_sensors = [polydata.GetNumberOfPoints()
                       for polydata in model.sensor_grids.data]
    # if grid is meshes
    else:
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
        data.path).iterdir() if result.suffix != '.json']

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

        if isinstance(legend_params.min, Autocalculate):
            legend.min = None
        else:
            legend.min = legend_params.min

        if isinstance(legend_params.max, Autocalculate):
            legend.max = None
        else:
            legend.max = legend_params.max

        if not legend.min and not legend.max:
            warnings.warn(
                f'For legend{data.object_type.value.capitalize()}, since min and max'
                ' values are not provided, those values will be auto calculated based'
                ' on data.'
            )

        legend.hide_legend = legend_params.hide_legend
        legend.orientation = legend_params.orientation
        legend.position = legend_params.position
        legend.width = legend_params.width
        legend.height = legend_params.height

        if isinstance(legend_params.color_count, int):
            legend.color_count = legend_params.color_count
        else:
            legend.color_count = None

        if isinstance(legend_params.label_count, int):
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
