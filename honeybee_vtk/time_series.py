"""Functions to load time series data."""

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


def _validate_folder_name(folder_path: pathlib.Path) -> str:
    """Find out if the folder name has hoy or moy at the end."""
    # TODO: This check should not be honeybee-vtk's responsibility. Remove at somepoint.
    return True if folder_path.stem[-3:].lower() == "moy" \
        or folder_path.stem[-3:].lower() == 'hoy' else False


def _validate_subfolder_names(folder_path: pathlib.Path) -> bool:
    """Find out if the subfolders names are numeric."""
    # TODO: This check should not be honeybee-vtk's responsibility. Remove at somepoint.
    return all([subfolder.name.isnumeric()
                for subfolder in folder_path.iterdir()])


def _load_point_in_time_data(
        folder_path: pathlib.Path, identifier: str, object_type: DataSetNames,
        model: Model, grid_type: str) -> Model:
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
        folder_path: pathlib.Path, identifier: str, object_type: DataSetNames,
        model: Model, grid_type: str, hbjson: str) -> Tuple[pathlib.Path, pathlib.Path]:
    """Write time steps to folders."""

    # create a temp folder to write the time steps
    temp_folder = pathlib.Path(tempfile.mkdtemp())
    print('Temp folder created')

    # create a folder to collect raw data
    raw_folder = temp_folder.joinpath('raw')
    raw_folder.mkdir()
    print('Raw folder created')

    for path in folder_path.iterdir():
        # create a honeybee-vtk model
        model = Model.from_hbjson(hbjson, load_grids=SensorGridOptions.Mesh)
        # load each time step data on a separate model
        model_with_data = _load_point_in_time_data(path, identifier, object_type,
                                                   model, grid_type)
        # use time step name to create a time step folder path
        time_step_path = raw_folder.joinpath(path.stem)
        # write the model to the time step folder
        model_with_data.to_point_in_time_folder(target=time_step_path)
        print(f'Time step {path.stem} written to folder.')

    print(temp_folder.stem)
    return temp_folder, raw_folder


def _move_data(time_step_folder: pathlib.Path, data_folder: pathlib.Path) -> None:
    """Move the data from the time step folder to the data folder."""
    for item in time_step_folder.iterdir():
        if item.is_dir():
            data = item.joinpath('data')
            for file in data.iterdir():
                file_destination = data_folder.joinpath(file.name)
                shutil.move(file, file_destination)
    print('Unique geometry and arrays moved to the data folder'
          f' for time step {time_step_folder.stem}.')


def _collect_data(temp_folder: pathlib.Path, raw_folder: pathlib.Path) -> None:
    """Collect unique geometry and arrays in a folder named "data"."""
    data_folder = temp_folder.joinpath('data')
    data_folder.mkdir()
    print('Data folder created.')

    for time_step_folder in raw_folder.iterdir():
        _move_data(time_step_folder, data_folder)


def _dataset_folders(temp_folder: pathlib.Path, raw_folder: pathlib.Path) -> None:
    """Write folders for all datasets except Grid and move index.json from raw folder."""
    first_time_step = raw_folder.iterdir().__next__()
    for ds in first_time_step.iterdir():
        if ds.is_dir() and ds.name != 'Grid':
            ds_path = temp_folder.joinpath(ds.stem)
            ds_path.mkdir()
            print(f'Folder for dataset {ds.stem} created.')

            src_index = ds.joinpath('index.json')
            dst_index = temp_folder.joinpath(ds.stem, 'index.json')
            shutil.move(src_index, dst_index)
            print(f'Index.json for dataset {ds.stem} moved to folder.')


def _grid_folder(temp_folder: pathlib.Path, raw_folder: pathlib.Path) -> None:
    """Write Grid folder."""
    grid_folder = temp_folder.joinpath('Grid')
    grid_folder.mkdir()
    print(f'Folder for dataset Grid created.')

    for time_step_folder in raw_folder.iterdir():
        # create time step folder
        grid_time_step_folder = temp_folder.joinpath('Grid', time_step_folder.stem)
        grid_time_step_folder.mkdir()
        print(f'Grid time step {time_step_folder.stem} folder created.')

        src_index = time_step_folder.joinpath('Grid', 'index.json')
        dst_index = grid_time_step_folder.joinpath('index.json')
        shutil.move(src_index, dst_index)
        print(f'Index.json moved to grid time step {time_step_folder.stem}.')


def _move_master_index(temp_folder: pathlib.Path, raw_folder: pathlib.Path) -> None:
    """Move the master index from the raw folder to the temp folder."""
    first_time_step = raw_folder.iterdir().__next__()
    src_index = first_time_step.joinpath('index.json')
    dst_index = temp_folder.joinpath('index.json')
    shutil.move(src_index, dst_index)
    print(f'Master Index.json moved to folder.')


def _nuke_raw(raw_folder: pathlib.Path) -> None:
    """Remove raw folder."""
    try:
        shutil.rmtree(raw_folder)
        print('Raw folder deleted.')
    except Exception:
        pass


def _update_data_paths(temp_folder: pathlib.Path) -> None:
    """Update path to data in each of the index.jsons except the Master index.json."""

    # path to data
    data_path = '../../data'

    # update path to data in all datasets except Grid
    for dir in temp_folder.iterdir():
        if dir.is_dir() and not dir.name == 'data' and not dir.name == 'Grid':
            index_json = dir.joinpath('index.json')
            with open(index_json, 'r') as file:
                data = json.load(file)
                data['points']['ref']['basepath'] = data_path
                data['polys']['ref']['basepath'] = data_path
            with open(index_json, 'w') as file:
                json.dump(data, file)
            print(f'Data path in index.json for {dir.name} updated.')

    # update path to data in Grid time step folders
    grid_folder = temp_folder.joinpath('Grid')
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
        print(f'Data path in index.json for time step {dir.name} updated in Grid.')


def _add_time_step_index(temp_folder: pathlib.Path) -> None:
    """Add an index.json to the Grid folder that maps all the time steps."""
    grid_folder = temp_folder.joinpath('Grid')
    time_series = TimeSeries(
        series=[
            TimeStep(url=dir.name, timeStep=int(dir.name)) for
            dir in grid_folder.iterdir()
        ]
    )
    index_path = grid_folder.joinpath('index.json')
    with open(index_path, 'w') as file:
        json.dump(time_series.dict(), file)
    print(f'Time step mapper index.json written to the Grid folder.')


def _update_grid_in_index(temp_folder: pathlib.Path) -> None:
    """Update grid object in the master index.json."""
    index_json = temp_folder.joinpath('index.json')
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
    print(f'Grid object updated in master index.json.')


def _append_animation_time_steps(temp_folder: pathlib.Path) -> None:
    """Append animation time steps to the master index.json."""
    index_json = temp_folder.joinpath('index.json')
    time_steps = [int(time_step.stem)
                  for time_step in temp_folder.joinpath('Grid').iterdir() if time_step.is_dir()]

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
        animation = Animation(timeSteps=[AnimationTimeStep(
            time=time_step, Grid=grid_obj) for time_step in time_steps])
        data['animation'] = animation.dict()

    with open(index_json, 'w') as file:
        json.dump(data, file)
    print(f'Animation time steps added to master index.json.')


def to_time_series_folder(
        folder_path: pathlib.Path, identifier: str, object_type: DataSetNames,
        model: Model, grid_type: str, hbjson: str) -> pathlib.Path:
    """Create a time series folder ready to be zipped as .vtkjs.

    Args:
        folder_path: Path to folder containing time series data.
        identifier: Identifier from the DataConfig object on the config file.
        object_type: object_type from the DataConfig object on the config file.
        model: A honeybee-vtk model.
        grid_type: A string representing the type of grid. Accepted values are
            'poinits' or 'meshes'.
        hbjson: Path to HBJSON file.

    Returns:
        A Pathlib path to the written folder.
    """

    # for the data provided as time series, validate the folder name and the subfolder
    # names
    if _validate_folder_name(folder_path) and _validate_subfolder_names(folder_path):
        print('Folder name and sub-folder names are fine.')
        # write a folder for each time step data
        temp_folder, raw_folder = _write_time_steps(
            folder_path, identifier, object_type, model, grid_type, hbjson)

        # collect unique geometry and arrays in a folder named "data"
        _collect_data(temp_folder, raw_folder)

        # create folders for dataset
        _dataset_folders(temp_folder, raw_folder)

        # create folder for grid
        _grid_folder(temp_folder, raw_folder)

        # move the index.json from the raw folder to the time step folder
        _move_master_index(temp_folder, raw_folder)

        # remove the raw folder
        _nuke_raw(raw_folder)

        # edit path to data in all index.json files
        _update_data_paths(temp_folder)

        # add index.json to grid folder
        _add_time_step_index(temp_folder)

        # Update in grid object in the scene object of the master index.json
        _update_grid_in_index(temp_folder)

        # append animation time steps to the master index.json
        _append_animation_time_steps(temp_folder)

    return temp_folder
