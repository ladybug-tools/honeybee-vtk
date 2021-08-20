"""Functions to validate and load data and legend parameters from a config file."""

from __future__ import annotations
import json
import pathlib
import warnings

from .types import DataSetNames
from .legend_parameter import Text
from .model import Model
from .vtkjs.schema import DisplayMode
from .scene import Scene
from .config import DataConfig, Autocalculate


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


def _load_data(folder_path: pathlib.Path, identifier: str, object_type: DataSetNames,
               model: Model, grid_type: str) -> None:
    """Load validated data on a honeybee-vtk model.

    This is a helper method to the public load_config method.

    Args:
        folder_path: A valid pathlib path to the folder with grid_info.json and data.
        identifier: A text string representing the identifier of the data in the config
            file.
        object_type: A DatasetNames object indicating the type of object on which data
            will be mounted.
        model: A honeybee-vtk model.
        grid_type: A string indicating whether the sensor grid in the model is made of
            points or meshes.
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

    ds = model.get_modeldataset(object_type)

    if grid_type == 'meshes':
        ds.add_data_fields(
            result, name=identifier, per_face=True)
        ds.color_by = identifier
        ds.display_mode = DisplayMode.SurfaceWithEdges
    else:
        ds.add_data_fields(
            result, name=identifier, per_face=False)
        ds.color_by = identifier
        ds.display_mode = DisplayMode.Points


def _load_legend_parameters(data: DataConfig, model: Model, scene: Scene) -> None:
    """Load legend_parameters.

    Args:
        data: A Dataconfig object.
        model: A honeybee-vtk model object.
        scene: A honeyebee-vtk scene object.
    """
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
            f'In data {data.identifier.capitalize()}, since min and max'
            ' values are not provided, those values will be auto calculated based'
            ' on data. \n'
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
    try:
        with open(json_path) as fh:
            config = json.load(fh)
    except json.decoder.JSONDecodeError:
        raise TypeError(
            'Not a valid json file.'
        )
    else:
        for json_obj in config.values():
            # check if model has grids loaded
            assert len(model.sensor_grids.data) > 0, 'Sensor grids are not loaded on'\
                ' this model. Reload them using grid options.'
            # validate config
            data = DataConfig.parse_obj(json_obj)
            # if data is requested
            if not data.hide:
                folder_path = pathlib.Path(data.path)
                identifier = data.identifier
                object_type = data.object_type
                grid_type = _get_grid_type(model)
                # Validate data if asked for
                if validation:
                    _validate_simulation_data(data, model, grid_type)
                # Load data
                _load_data(folder_path, identifier, object_type, model, grid_type)
                # If legend is requested and legend parameters are provided
                # Legend will only be used in export-images command
                if legend and data.legend_parameters:
                    _load_legend_parameters(data, model, scene)
            else:
                warnings.warn(
                    f'Data for {data.identifier} is not loaded.'
                )

    return model
