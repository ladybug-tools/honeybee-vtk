"""Data json schema and validation for the config file."""

from __future__ import annotations
import json
import os
import pathlib
import warnings

from typing import List, Union, Tuple, TypeVar
from pydantic import BaseModel, validator, Field, constr, conint
from pydantic.types import confloat, conlist
from .types import DataSetNames
from .legend_parameter import ColorSets, Text, DecimalCount, Orientation, LegendParameter
from .model import Model
from ._helper import get_line_count, get_min_max
from .vtkjs.schema import DisplayMode
from .scene import Scene


class InputFile(BaseModel):
    """Config for the input file to be consumed by the config command."""
    paths: List[str] = Field(
        description='Paths to the result folders.')

    identifiers: List[str] = Field(
        description='Identifiers for the simulation data that will be mounted on the'
        ' model. The length of this list must match the length of paths.')

    units: List[str] = Field(
        description='Units for the simulation data that will be mounted on the'
        ' model. The length of this list must match the length of paths.')

    @validator('identifiers', 'units')
    def check_length(cls, v, values):
        """Check that the length of identifiers and units match the length of paths."""
        if len(values['paths']) != len(v):
            raise ValueError('The length of paths, identifiers, and units must match.')
        return v


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
        0,
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
    """data-config for simulation results you'd like to load on a honeybee-vtk model."""

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

    @validator('legend_parameters')
    def check_pos_against_width_height(cls, v: LegendConfig, values) -> LegendConfig:
        id = values['identifier']
        if v.width >= 0.5 and v.position[0] >= 0.5 and v.width > v.position[0]:
            raise ValueError(
                f'Width of legend {id}, {v.width}'
                f' cannot be greater than the position of legend in X direction'
                f' {v.position[0]}.'
                ' Either update the position in X direction or update the'
                ' width of the legend. \n'
            )
        if v.height >= 0.5 and v.position[1] >= 0.5 and v.height > v.position[1]:
            raise ValueError(
                f'Height of legend {id}, {v.height}'
                f' cannot be greater than the position of legend in Y direction'
                f' {v.position[1]}.'
                ' Either update the position in Y direction or update the'
                ' height of the legend. \n'
            )
        return v


class Config(BaseModel):
    """Config for simulation results you'd like to load on a honeybee-vtk model."""
    data: List[DataConfig] = Field(
        description='List of data-config objects that define the data to be loaded on'
        ' the model.'
    )


def _get_grid_type(model: Model) -> str:
    """Get the type of grid in the model

    Args:
        model(Model): A honeybee-vtk model.

    Returns:
        A string indicating whether the model has points and meshes.
    """

    if model.sensor_grids.data[0].GetNumberOfCells() == 1:
        return 'points'
    else:
        return 'meshes'


def _validate_simulation_data(data: DataConfig, model: Model, grid_type: str) -> None:
    """Match result data with the sensor grids in the model.

    It will be checked if the number of data files and the names of the
    data files match with the grid identifiers. This function does not support validating
    result data for other than sensor grids as of now.

    This is a helper method to the public load_config method.

    Args:
        data: A DataConfig object.
        model: A honeybee-vtk model.
        grid_type: A string indicating whether the model has points and meshes.
    """
    # file path to the json file
    grids_info_json = pathlib.Path(data.path).joinpath('grids_info.json')

    # read the json file
    with open(grids_info_json) as fh:
        grids_info = json.load(fh)

    # TODO: Make sure to remove this limitation. A user should not have to always
    # TODO: load all the grids
    assert len(model.sensor_grids.data) == len(grids_info), 'The number of result'\
        f' files {len(grids_info)} does for {data.identifier} does not match'\
        f' the number of sensor grids in the model {len(model.sensor_grids.data)}.'

    # match identifiers of the grids with the identifiers of the result files
    grids_model_identifiers = [grid.identifier for grid in model.sensor_grids.data]
    grids_info_identifiers = [grid['full_id'] for grid in grids_info]
    assert grids_model_identifiers == grids_info_identifiers, 'The identifiers of'\
        ' the sensor grids in the model do not match the identifiers of the grids'\
        f' in the grids_info.json for {data.identifier}.'

    # make sure length of each file matches the number of sensors in grid
    file_lengths = [grid['count'] for grid in grids_info]

    # check if the grid data is meshes or points
    # if grid is sensors
    if grid_type == 'points':
        num_sensors = [polydata.GetNumberOfPoints()
                       for polydata in model.sensor_grids.data]
    # if grid is meshes
    else:
        num_sensors = [polydata.GetNumberOfCells()
                       for polydata in model.sensor_grids.data]

    # lastly check if the length of a file matches the number of sensors or meshes on grid
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


def _load_data(folder_path: pathlib.Path, identifier: str, model: Model,
               grid_type: str, legend_range: List[Union[float, int]]) -> None:
    """Load validated data on a honeybee-vtk model.

    This is a helper method to the public load_config method.

    Args:
        folder_path: A valid pathlib path to the folder with grid_info.json and data.
        identifier: A text string representing the identifier of the data in the config
            file.
        model: A honeybee-vtk model.
        grid_type: A string indicating whether the sensor grid in the model is made of
            points or meshes.
        legend_range: A list of min and max values of the legend parameters provided by
            the user in the config file.
    """
    grids_info_json = folder_path.joinpath('grids_info.json')
    with open(grids_info_json) as fh:
        grids_info = json.load(fh)

    # grid identifier from grids_info.json
    file_names = [grid['identifier'] for grid in grids_info]

    # finding file extension for grid results
    for path in folder_path.iterdir():
        if path.stem == file_names[0]:
            extension = path.suffix
            break

    # file paths to the result files
    file_paths = [folder_path.joinpath(name+extension)
                  for name in file_names]

    result = []
    for file_path in file_paths:
        res_file = pathlib.Path(file_path)
        grid_res = [float(v)
                    for v in res_file.read_text().splitlines()]
        result.append(grid_res)

    ds = model.get_modeldataset(DataSetNames.grid)

    if grid_type == 'meshes':
        ds.add_data_fields(
            result, name=identifier, per_face=True, data_range=legend_range)
        ds.color_by = identifier
        ds.display_mode = DisplayMode.SurfaceWithEdges
    else:
        ds.add_data_fields(
            result, name=identifier, per_face=False, data_range=legend_range)
        ds.color_by = identifier
        ds.display_mode = DisplayMode.Points


def _get_legend_range(data: DataConfig) -> List[Union[float, int]]:
    """Read and get legend min and max values from data if provided by the user.

    The value provided by this function is processed and validated in _get_data_range
    function in the type module.

    Args:
        data (DataConfig): A Dataconfig object.

    Returns:
        A list of two numbers representing min and max values for data.
    """
    if data.legend_parameters:
        legend_params = data.legend_parameters

        if isinstance(legend_params.min, Autocalculate):
            min = None
        else:
            min = legend_params.min

        if isinstance(legend_params.max, Autocalculate):
            max = None
        else:
            max = legend_params.max

        return [min, max]


def _load_legend_parameters(data: DataConfig, model: Model, scene: Scene,
                            legend_range: List[Union[float, int]]) -> None:
    """Load legend_parameters.

    Args:
        data: A Dataconfig object.
        model: A honeybee-vtk model object.
        scene: A honeyebee-vtk scene object.
        legend_range: A list of min and max values of the legend parameters provided by
            the user in the config file.
    """
    legend_params = data.legend_parameters
    legend = scene.legend_parameter(data.identifier)

    legend.colors = legend_params.color_set
    legend.unit = data.unit
    if legend_range:
        legend.min, legend.max = legend_range
    else:
        legend.min, legend.max = [None, None]
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


def load_config(json_path: str, model: Model, scene: Scene,
                validation: bool = False, legend: bool = False) -> Model:
    """Mount data on model from config json.

    Args:
        json_path: File path to the config json file.
        model: A honeybee-vtk model object.
        scene: A honeybee-vtk scene object.
        validation: A boolean indicating whether to validate the data before loading.
        legend: A boolean indicating whether to load legend parameters.

    Returns:
        A honeybee-vtk model with data loaded on it.
    """
    assert len(model.sensor_grids.data) > 0, 'Sensor grids are not loaded on'\
        ' this model. Reload them using grid options.'

    config_dir = pathlib.Path(json_path).parent

    try:
        with open(json_path) as fh:
            config = json.load(fh)
    except json.decoder.JSONDecodeError:
        raise TypeError(
            'Not a valid json file.'
        )
    else:
        for json_obj in config['data']:
            # validate config
            data = DataConfig.parse_obj(json_obj)
            # only if data is requested move forward.
            if not data.hide:
                folder_path = pathlib.Path(data.path)
                if not folder_path.is_dir():
                    folder_path = config_dir.joinpath(
                        folder_path).resolve().absolute()
                    data.path = folder_path.as_posix()
                    if not folder_path.is_dir():
                        raise FileNotFoundError(
                            f'No folder found at {data.path}')
                identifier = data.identifier
                grid_type = _get_grid_type(model)
                # Validate data if asked for
                if validation:
                    _validate_simulation_data(data, model, grid_type)
                # get legend range if provided by the user
                legend_range = _get_legend_range(data)
                # Load data
                _load_data(folder_path, identifier, model, grid_type, legend_range)
                # Load legend parameters
                _load_legend_parameters(data, model, scene, legend_range)
            else:
                warnings.warn(
                    f'Data for {data.identifier} is not loaded.'
                )
    return model
