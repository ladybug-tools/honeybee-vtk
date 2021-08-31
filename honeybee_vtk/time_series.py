"""Functions to load time series data."""

from honeybee_vtk.config import DataConfig
import pathlib
import tempfile
import json
import shutil
import copy
from typing import List, Dict, Tuple
from copy import copy
from .model import Model
from .types import DataSetNames
from .vtkjs.schema import DisplayMode, SensorGridOptions, TimeStep, TimeSeries, \
    AnimationTimeStep, Animation


def _validate_folder_name(folder_path: pathlib.Path) -> bool:
    """Find out if the folder name has 'hoy' or 'moy' at the end."""
    # TODO: This check should not be honeybee-vtk's responsibility. Remove at somepoint.
    return True if folder_path.stem[-3:].lower() == "moy" \
        or folder_path.stem[-3:].lower() == 'hoy' else False


def _validate_subfolder_names(folder_path: pathlib.Path) -> bool:
    """Find out if the subfolders names are numeric."""
    # TODO: This check should not be honeybee-vtk's responsibility. Remove at somepoint.
    return all([subfolder.name.isnumeric()
                for subfolder in folder_path.iterdir()])


def _load_point_in_time_data(
        folder_path: pathlib.Path, identifier: str, object_type: DataSetNames, model: Model,
        grid_type: str) -> Model:
    """Load validated point-in-time data on a honeybee-vtk model.

    This is a helper method to the public load_config method.

    Args:
        folder_path: Path to the folder where the point in time data is stored.
            This folder must also have the grid_info.json file.
        identifier: Identifier of the data in the config file.
        object_type: Object_type of the data in the config file.
        model: A honeybee-vtk model.
        grid_type: A string indicating whether the sensor grid in the model is made of
            points or meshes.

    Returns:
        A honeybee-vtk model with the data loaded.
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

    return model


def _write_time_steps(
        time_series_folder: pathlib.Path, data: DataConfig, model: Model, grid_type: str,
        hbjson: str) -> Tuple[pathlib.Path, pathlib.Path]:
    """Write a point-in-time folder for each time steps and the time_series_folder.

    Args:
        time_series_folder: Path to the temp folder where all files and folders will be 
            written during the process of creating a time series vtkjs file.
        data: A Dataconfig object from the config file.
        folder_path: Path from the config file.
        identifier: Identifier of the data in the config file.
        object_type: Object_type of the data in the config file.
        model: A honeybee-vtk model.
        grid_type: type of grid as a string. Accepted values are 'points' or 'meshes'.
        hbjson: Path to the HBJSON file.

    Returns:
        A path to the raw_folder where each of the initial point-in-time folder is
            written. 
    """
    identifier = data.identifier
    object_type = data.object_type

    # create a folder to collect raw data
    raw_folder = time_series_folder.joinpath('raw')
    raw_folder.mkdir()

    folder_path = pathlib.Path(data.path)
    for path in folder_path.iterdir():
        # create a honeybee-vtk model
        model = Model.from_hbjson(hbjson, load_grids=SensorGridOptions.Mesh)
        # load each time step data on a separate model
        model_with_data = _load_point_in_time_data(
            path, identifier, object_type, model, grid_type)
        # use time step name to create a time step folder path
        time_step_path = raw_folder.joinpath(path.stem)
        # write the model to the time step folder
        model_with_data.to_point_in_time_folder(target=time_step_path)

    return raw_folder


def _move_data(point_in_time_folder: pathlib.Path, data_folder: pathlib.Path) -> None:
    """Migrate geometry and data.

    Migrate unique geometry and data from each point in time folder to the 'data' folder
    inside the time_series_folder.

    Args:
        point_in_time_folder: Path to a point in time folder
        data_folder: Path to a folder named 'data' inside the time_series_folder.
    """
    for item in point_in_time_folder.iterdir():
        if item.is_dir():
            data = item.joinpath('data')
            for file in data.iterdir():
                file_destination = data_folder.joinpath(file.name)
                shutil.move(file, file_destination)


def _collect_data(time_series_folder: pathlib.Path, raw_folder: pathlib.Path) -> None:
    """Collect geometry and data inside the 'data' folder in time_series_folder.

    Create a 'data' foder inside time_series_folder and move unique geometry and data
    from each of the point_in_time_folder to the 'data' folder.

    Args:
        time_series_folder: Path to the temp folder where all files and folders will be 
            written during the process of creating a time series vtkjs file.
        raw_folder: Path to the folder where all point_in_time folders are written.
    """
    data_folder = time_series_folder.joinpath('data')
    data_folder.mkdir()

    for point_in_time_folder in raw_folder.iterdir():
        _move_data(point_in_time_folder, data_folder)


def _dataset_folders(time_series_folder: pathlib.Path, raw_folder: pathlib.Path) -> None:
    """Write a folders for each dataset except Grid.

    In time_series_folder, write folders for all datasets except Grid and move
    index.json for each of the datasets from the raw_folder.

    Args:
        time_series_folder: Path to the temp folder where all files and folders will be 
            written during the process of creating a time series vtkjs file.
        raw_folder: Path to the folder where all point_in_time folders are written.
    """
    # only first time step is needed to know which datasets to write
    first_time_step = raw_folder.iterdir().__next__()

    for ds in first_time_step.iterdir():
        if ds.is_dir() and ds.name != 'Grid':
            ds_path = time_series_folder.joinpath(ds.stem)
            ds_path.mkdir()

            src_index = ds.joinpath('index.json')
            dst_index = time_series_folder.joinpath(ds.stem, 'index.json')
            shutil.move(src_index, dst_index)


def _grid_folder(time_series_folder: pathlib.Path, raw_folder: pathlib.Path) -> None:
    """Write Grid dataset folder.

    Args:
        time_series_folder: Path to the temp folder where all files and folders will be 
            written during the process of creating a time series vtkjs file.
        raw_folder: Path to the folder where all point_in_time folders are written.
    """
    grid_folder = time_series_folder.joinpath('Grid')
    grid_folder.mkdir()

    for point_in_time_folder in raw_folder.iterdir():
        # create time step folder
        grid_time_step_folder = time_series_folder.joinpath(
            'Grid', point_in_time_folder.stem)
        grid_time_step_folder.mkdir()

        src_index = point_in_time_folder.joinpath('Grid', 'index.json')
        dst_index = grid_time_step_folder.joinpath('index.json')
        shutil.move(src_index, dst_index)


def _move_master_index(time_series_folder: pathlib.Path, raw_folder: pathlib.Path) -> None:
    """Migrate master index.json to the time_series_folder.

    Migrate master index.json from the first point in time folder to the
    time_series_folder.

    Args:
        time_series_folder: Path to the temp folder where all files and folders will be 
            written during the process of creating a time series vtkjs file.
        raw_folder: Path to the folder where all point_in_time folders are written.
    """
    # Only index.json from the first point in time folder is needed
    first_time_step = raw_folder.iterdir().__next__()
    src_index = first_time_step.joinpath('index.json')
    dst_index = time_series_folder.joinpath('index.json')
    shutil.move(src_index, dst_index)


def _nuke_raw(raw_folder: pathlib.Path) -> None:
    """Delete the raw folder.

    Args:
        raw_folder: Path to the folder where all point_in_time folders are written.
    """
    try:
        shutil.rmtree(raw_folder)
    except Exception:
        pass


def _update_data_paths(time_series_folder: pathlib.Path) -> None:
    """Update path to data in each of the index.jsons except the Master index.json.

    Args:
        time_series_folder: Path to the temp folder where all files and folders will be 
            written during the process of creating a time series vtkjs file.
    """

    # path to data
    data_path = '../../data'

    # update path to data in all datasets except Grid
    for dir in time_series_folder.iterdir():
        if dir.is_dir() and not dir.name == 'data' and not dir.name == 'Grid':
            index_json = dir.joinpath('index.json')
            with open(index_json, 'r') as file:
                data = json.load(file)
                data['points']['ref']['basepath'] = data_path
                data['polys']['ref']['basepath'] = data_path
            with open(index_json, 'w') as file:
                json.dump(data, file)

    # update path to data in Grid time step folders
    grid_folder = time_series_folder.joinpath('Grid')
    for dir in grid_folder.iterdir():
        index_json = dir.joinpath('index.json')
        with open(index_json, 'r') as file:
            data = json.load(file)
            data['points']['ref']['basepath'] = data_path
            data['polys']['ref']['basepath'] = data_path
            if 'cellData' in data:
                data['cellData']['arrays'][0]['data']['ref']['basepath'] = data_path
            elif 'pointData' in data:
                data['pointData']['arrays'][0]['data']['ref']['basepath'] = data_path
        with open(index_json, 'w') as file:
            json.dump(data, file)


def _add_time_step_index(time_series_folder: pathlib.Path) -> None:
    """Add an index.json to the Grid folder that maps all the time steps.

    Args:
        time_series_folder: Path to the temp folder where all files and folders will be 
            written during the process of creating a time series vtkjs file.
    """
    grid_folder = time_series_folder.joinpath('Grid')
    time_series = TimeSeries(
        series=[
            TimeStep(url=dir.name, timeStep=int(dir.name)) for
            dir in grid_folder.iterdir()
        ]
    )
    index_path = grid_folder.joinpath('index.json')
    with open(index_path, 'w') as file:
        json.dump(time_series.dict(), file)


def _update_grid_in_index(time_series_folder: pathlib.Path) -> None:
    """Update grid object in the master index.json.

    Make changes to the grid object in the scene of the master index.json.

    Args:
        time_series_folder: Path to the temp folder where all files and folders will be 
            written during the process of creating a time series vtkjs file.
    """
    index_json = time_series_folder.joinpath('index.json')
    with open(index_json, 'r') as file:
        data = json.load(file)
        for item in data['scene']:
            if item['name'] == 'Grid':
                item['id'] = 'Grid'
                item['type'] = 'httpDataSetSeriesReader'
                item.pop('httpDataSetReader')
                item['httpDataSetSeriesReader'] = {'url': 'Grid'}
    with open(index_json, 'w') as file:
        json.dump(data, file)


def _append_animation_time_steps(time_series_folder: pathlib.Path) -> None:
    """Append animation time steps to the master index.json.

    Args:
        time_series_folder: Path to the temp folder where all files and folders will be 
            written during the process of creating a time series vtkjs file.
    """
    index_json = time_series_folder.joinpath('index.json')
    time_steps = [int(time_step.stem)
                  for time_step in time_series_folder.joinpath('Grid').iterdir()
                  if time_step.is_dir()]

    grid_obj = {}
    with open(index_json, 'r') as file:
        data = json.load(file)
        # extract grid object from index.json and remove keys from it so that it can be
        # used in animation time steps.
        for item in data['scene']:
            if item['name'] == 'Grid':
                grid_item = copy(item)
                keys = ['name', 'id', 'type', 'httpDataSetSeriesReader']
                [grid_item.pop(key) for key in keys]
                grid_obj['Grid'] = grid_item

        # add animation time steps to index.json
        animation = Animation(
            timeSteps=[AnimationTimeStep(time=time_step, Grid=grid_obj)
                       for time_step in time_steps])
        data['animation'] = animation.dict()

    with open(index_json, 'w') as file:
        json.dump(data, file)


def to_time_series_folder(data: DataConfig, model: Model, grid_type: str,
                          hbjson: str) -> pathlib.Path:
    """Create a time series folder ready to be zipped as a .vtkjs file.

    Args:
        data: A Dataconfig object from the config file.
        model: A honeybee-vtk model.
        grid_type: A string representing the type of grid. Accepted values are
            'poinits' or 'meshes'.
        hbjson: Path to HBJSON file.

    Returns:
        Path to the written time_series_folder.
    """
    folder_path = pathlib.Path(data.path)
    # for the data provided as time series, validate the folder name and the subfolder
    # names
    if _validate_folder_name(folder_path) and _validate_subfolder_names(folder_path):

        # write the time_series_folder as a temp_folder
        time_series_folder = pathlib.Path(tempfile.mkdtemp())

        # write a point_in_time_folder for each time step data
        raw_folder = _write_time_steps(
            time_series_folder, data, model, grid_type, hbjson)

        # collect unique geometry and arrays in a folder named "data"
        _collect_data(time_series_folder, raw_folder)

        # create folders for datasets except grid
        _dataset_folders(time_series_folder, raw_folder)

        # create folder for grid dataset
        _grid_folder(time_series_folder, raw_folder)

        # move the one of the master index.json from the raw_folder to the
        # time_series_folder
        _move_master_index(time_series_folder, raw_folder)

        # remove the raw_folder
        _nuke_raw(raw_folder)

        # edit path to data in all index.json files
        _update_data_paths(time_series_folder)

        # add index.json to grid folder
        _add_time_step_index(time_series_folder)

        # Update in grid object in the scene object of the master index.json
        _update_grid_in_index(time_series_folder)

        # append animation time steps to the master index.json
        _append_animation_time_steps(time_series_folder)

    else:
        raise ValueError(
            'The time step folder name must end with "HOY" or "MOY" and also, the names'
            ' of all the subfolders must be numeric.'
        )
    return time_series_folder
