"""Function to generate images from time series data."""

import json
import pathlib
import tempfile
import shutil
import os

from pandas import DataFrame
from typing import List
from ladybug.dt import DateTime
from ladybug.color import Colorset

from .config import Config, DataConfig, LegendConfig
from .model import Model, SensorGridOptions
from .vtkjs.schema import DisplayMode
from .text_actor import TextActor


def get_datetimes(path: pathlib.Path) -> List[DateTime]:
    """Read a .txt file with time stamps and return a list of hoys."""
    with open(path, 'r') as f:
        return [DateTime.from_hoy(float(line.strip())) for line in f]


def get_timestamp_indexes(time_stamp_path: pathlib.Path, st_datetime: DateTime,
                          end_datetime: DateTime) -> List[int]:

    time_stamp_datetimes = get_datetimes(time_stamp_path)
    return [count for count, datetime in enumerate(time_stamp_datetimes) if
            st_datetime <= datetime <= end_datetime]


def get_res_file_extension(path: pathlib.Path, grids_info: List[dict]) -> str:
    """Get the file extension of the result file."""

    first_grid_id: str = grids_info[0]['identifier']

    for item in list(path.iterdir()):
        if item.stem == first_grid_id:
            return item.suffix


def get_res_paths(path: pathlib.Path, grids_info_path: pathlib.Path) -> List[pathlib.Path]:
    try:
        with open(grids_info_path) as fh:
            grids_info = json.load(fh)
    except json.decoder.JSONDecodeError:
        raise TypeError(
            'Not a valid json file.'
        )

    res_extension = get_res_file_extension(path, grids_info)
    return [path.joinpath(f'{grid["identifier"]}{res_extension}') for grid in grids_info]


def extract_column(path: pathlib.Path, index: int) -> List[int]:
    """Extract a column from a result file."""
    with open(path, 'r') as f:
        lines = f.readlines()
        df = DataFrame([line.strip().split('\t') for line in lines])

    try:
        return [int(val) for val in df[index].values]
    except KeyError:
        raise KeyError(f'Column {index} does not exist.')


def write_res_file(res_path: pathlib.Path, data: List[int],
                   target_folder: pathlib.Path = pathlib.Path('.')):
    file_path = pathlib.Path(target_folder).joinpath(f'{res_path.stem}.res')
    with open(file_path, 'w') as f:
        for val in data:
            f.write(f'{val}\n')


def write_config(target_folder: pathlib.Path, data_path: pathlib.Path):
    """Write a config file for the simulation."""

    config = Config(data=[
        DataConfig(identifier='sun-up-hours', path=data_path.as_posix(),
                   object_type='grid', unit='hours', hide=False,
                   legend_parameters=LegendConfig(color_set='original'))
    ])

    config_path = target_folder.joinpath('config.json')
    with open(config_path, 'w') as f:
        f.write(config.json())


def export_timestep_images(hbjson_path: str, time_series_folder_path: str,
                           timestamp_file_name: str,
                           st_datetime: DateTime, end_datetime: DateTime,
                           target_folder: str = '.'):
    path = pathlib.Path(time_series_folder_path)
    assert path.exists(), 'Path does not exist.'

    timestamp_file_path = path.joinpath(f'{timestamp_file_name}.txt')
    assert timestamp_file_path.exists(), f'File with name {timestamp_file_name}'
    ' does not exist.'

    timestamp_indexes = get_timestamp_indexes(timestamp_file_path, st_datetime,
                                              end_datetime)

    grids_info_path = path.joinpath('grids_info.json')
    res_paths = get_res_paths(path, grids_info_path)

    for index in timestamp_indexes:
        temp_folder = pathlib.Path(tempfile.mkdtemp())
        print(f'Temp folder is {temp_folder}')
        index_folder = pathlib.Path(temp_folder).joinpath(str(index))
        os.mkdir(index_folder)

        index_grids_info_path = pathlib.Path(index_folder).joinpath('grids_info.json')
        shutil.copy(grids_info_path, index_grids_info_path)
        for res_path in res_paths:
            data = extract_column(res_path, index)
            write_res_file(res_path, data, index_folder)
        write_config(temp_folder, index_folder)
        config_path = pathlib.Path(temp_folder).joinpath('config.json')
        model = Model.from_hbjson(hbjson_path, SensorGridOptions.Mesh)
        model.to_grid_images(folder='.', config=config_path,
                             grid_display_mode=DisplayMode.Shaded,
                             text_actor=TextActor(text=f'Hour {index}'),
                             image_name=f'{index}')
