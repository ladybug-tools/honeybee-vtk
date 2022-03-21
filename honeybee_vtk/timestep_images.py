"""Function to generate images from time series data."""

import json
import pathlib
import tempfile
import shutil
import os
import vtk

from pandas import DataFrame
from typing import List, Tuple, Dict, Union
from ladybug.dt import DateTime
from ladybug.color import Color


from .config import Config, DataConfig, Autocalculate, Period, Periods
from .model import Model, SensorGridOptions
from .vtkjs.schema import DisplayMode
from .text_actor import TextActor


def _get_datetimes(path: pathlib.Path) -> List[DateTime]:
    """Read a .txt file with time stamps and return a list of Datetime object.

    Here, time stamp can be HOY, MOY, or DOY.

    Args:
        path: Path to the .txt file.

    Returns:
        A list of Datetime objects.
    """
    with open(path, 'r') as f:
        return [DateTime.from_hoy(float(line.strip())) for line in f]


def _get_timestamp_indexes(time_stamp_path: pathlib.Path,
                           period: Tuple[DateTime, DateTime]) -> Tuple[
                               List[int], List[DateTime]]:
    """Get the indexes of the timestamps in the time stamp file between two Datetimes.

    This function will give you all the Datetime objects for all the time stamps that
    exist between the start and end Datetime objects.

    Args:
        time_stamp_path: Path to the time stamp file.
        period: A tuple of two Datetime objects.

    Returns:
        A tuple of two lists.

        - The first list is a list of indexes of the timestamps in the time stamp file.

        - The second list is a list of corresponding Datetime objects.
    """
    st_datetime, end_datetime = period
    time_stamp_datetimes = _get_datetimes(time_stamp_path)
    index, datetimes = [], []
    for count, datetime in enumerate(time_stamp_datetimes):
        if st_datetime <= datetime <= end_datetime:
            index.append(count)
            datetimes.append(datetime)
    return index, datetimes


def _get_res_file_extension(path: pathlib.Path, grids_info: List[dict]) -> str:
    """Get the common file extension of the result files in the folder.

    Args:
        path: Path to the folder.
        grids_info: A list of grids info objects.

    Returns:
        The common file extension of the result files in the folder.
    """

    first_grid_id: str = grids_info[0]['identifier']

    for item in list(path.iterdir()):
        if item.stem == first_grid_id:
            return item.suffix


def _get_result_paths(path: pathlib.Path,
                      grids_info_path: pathlib.Path) -> List[pathlib.Path]:
    """Get file paths of the result files in the folder.

    Args:
        path: Path to the folder.
        grids_info_path: Path to the grids info.json file.

    Returns:
        A list of file paths to the result files.
    """
    try:
        with open(grids_info_path) as fh:
            grids_info = json.load(fh)
    except json.decoder.JSONDecodeError:
        raise TypeError(
            'Not a valid json file.'
        )

    res_extension = _get_res_file_extension(path, grids_info)
    return [path.joinpath(f'{grid["identifier"]}{res_extension}') for grid in grids_info]


def _extract_column(path: pathlib.Path, index: int) -> List[int]:
    """Extract a column from a result file.

    This function first turns the file into a pandas DataFrame and then extracts the
    column at the given index.

    Args:
        path: Path to the result file.
        index: Index of the column to extract.

    Returns:
        A list of integer values.
    """
    with open(path, 'r') as f:
        lines = f.readlines()
        df = DataFrame([line.strip().split('\t') for line in lines])

    try:
        return [int(val) for val in df[index].values]
    except KeyError:
        raise KeyError(f'Column {index} does not exist.')


def _write_res_file(res_path: pathlib.Path, data: List[int],
                    target_folder: pathlib.Path = pathlib.Path('.')) -> None:
    """Write a list of integer values to a .res file.

    Args:
        res_path: Path to the result file.
        data: A list of integer values.
        target_folder: Path to the folder to write the result file.
            Defaults to the current folder.
    """
    file_path = pathlib.Path(target_folder).joinpath(f'{res_path.stem}.res')
    with open(file_path, 'w') as f:
        for val in data:
            f.write(f'{val}\n')


def _validate_config(config_path: str) -> DataConfig:
    """Validate the config file.

    Args:
        config_path: Path to the config file.

    Returns:
        A DataConfig object.
    """
    try:
        with open(config_path) as fh:
            config = json.load(fh)
    except json.decoder.JSONDecodeError:
        raise TypeError(
            'Not a valid json file.'
        )
    else:
        assert len(config['data']) == 1, 'Only one object is needed in the this'\
            ' config file.'
        data = DataConfig.parse_obj(config['data'][0])
        assert not data.hide, 'Make sure that in the config file you have not indicated'\
            ' the data to be hidden.'
        return data


def _write_config(data: DataConfig, target_folder: pathlib.Path,
                  data_path: pathlib.Path) -> pathlib.Path:
    """Write a config file to be consumed by honeybee-vtk.

    Args:
        data: A DataConfig object.
        target_folder: Path to the folder to write the config file.
        data_path: Path to folder with grids_info.json and .res files.

    this function will replace the path property in the Dataconfig object with
    the path to the data folder.

    Returns:
        Path to the config file.
    """

    data.path = data_path.as_posix()
    config = Config(data=[data])

    config_path = target_folder.joinpath('config.json')
    with open(config_path, 'w') as f:
        f.write(config.json())

    return config_path


def _create_folders(parent_temp_folder: pathlib.Path,
                    index: int) -> Tuple[pathlib.Path, pathlib.Path]:
    """Create a temp folder and an Index folder for the current index.

    Args:
        parent_temp_folder: Path to the parent temp folder.
        index: Index of the time stamp in the time stamps file.

    Returns:
        A tuple of paths to the temp folder and the Index folder.
    """

    temp_folder = pathlib.Path(tempfile.mkdtemp(dir=parent_temp_folder.as_posix()))
    index_folder = temp_folder.joinpath(str(index))
    os.mkdir(index_folder)
    return temp_folder, index_folder


def _copy_grids_info(grids_info_path: pathlib.Path, index_folder: pathlib.Path) -> None:
    """Copy grids_info.json to the Index folder."""
    index_grids_info_path = pathlib.Path(index_folder).joinpath('grids_info.json')
    shutil.copy(grids_info_path, index_grids_info_path)


def _write_res_files(result_paths: List[pathlib.Path], index: int,
                     index_folder: pathlib.Path) -> None:
    """Write .res files to the Index folder.

    For each Index of the time stamp in the time stamp file. Write a .res for each of
    the result files in the folder. The number of these result files would be equal
    to the number of grids in the grids_info.json file.

    Args:
        res_paths: List of file paths to the result files

    """
    for result_path in result_paths:
        data = _extract_column(result_path, index)
        _write_res_file(result_path, data, index_folder)


def _get_data_without_thresholds(data: DataConfig) -> DataConfig:
    """Remove threshold from a DataConfig object.

    This is useful in the dry run where the model needs to be run without the
    thresholds.

    Args:
        data: A DataConfig object.

    Returns:
        A DataConfig object without thresholds.
    """
    data_without_thresholds = data.copy(deep=True)
    data_without_thresholds.upper_threshold = Autocalculate()
    data_without_thresholds.lower_threshold = Autocalculate()
    return data_without_thresholds


def _get_grid_camera_dict(data: DataConfig,
                          grid_display_mode: DisplayMode,
                          temp_folder: pathlib.Path,
                          index_folder: pathlib.Path, hbjson_path: str,
                          target_folder: str, index: int) -> Union[
        None, Dict[str, vtk.vtkCamera]]:
    """Get a dictionary of grid identifiers and vtkCameras.

    A dry run is done without applying thresholds and vtkCameras are extracted from
    this run for each of the grids.

    Args:
        data: DataConfig object from the config file.
        grid_display_mode: Display mode of the grids. Defaults to Shaded.
        temp_folder: Path to the temp folder.
        index_folder: Path to the Index folder.
        hbjson_path: Path to the HBJSON file.
        target_folder: Path to the folder to write the images. Defaults to the current
            folder.
        index: Index of the time stamp in the time stamps file.

    Returns:
        A dictionary of grid identifiers and vtkCameras or None.
    """
    if not isinstance(data.upper_threshold, Autocalculate) or \
            not isinstance(data.lower_threshold, Autocalculate):
        config_path = _write_config(
            _get_data_without_thresholds(data), temp_folder, index_folder)
        model = Model.from_hbjson(hbjson_path, SensorGridOptions.Mesh)
        return model.to_grid_images(folder=target_folder,
                                    config=config_path.as_posix(),
                                    grid_display_mode=grid_display_mode,
                                    text_actor=TextActor(
                                        text=f'Hour {index}'),
                                    image_name=f'{index}', extract_camera=True)


def export_timestep_images(hbjson_path: str, config_path: str,
                           timestamp_file_name: str,
                           periods: List[Tuple[DateTime, DateTime]] = [
                               (DateTime(6, 21, 8), DateTime(6, 21, 19))],
                           grid_colors: List[Color] = [Color(249, 7, 3)],
                           grid_display_mode: DisplayMode = DisplayMode.Shaded,
                           target_folder: str = '.',
                           grid_filter: List[str] = None,
                           text_actor: TextActor = None,
                           label_images: bool = True,
                           image_width: int = 1920,
                           image_height: int = 1088) -> str:
    """Export images of grids for each time step in the time stamps file.

    This function will find all the time stamps between the start and end datetimes
    in the time stamps file and export images of each grids for each time step.

    Args:
        hbjson_path: Path to the HBJSON file.
        config_path: Path to the config file.
        timestamp_file_name: Name of the time stamps file as a string. This is simply
            used to find the time stamps file.
        periods: A list of tuple of start and end datetimes. Defaults to a single
            period from 8 am to 7 pm on 21st of June.
        grid_display_mode: Display mode of the grids. Defaults to Shaded.
        target_folder: Path to the folder to write the images. Defaults to the current
            folder.
        grid_filter: A list of grid identifiers to export images of those grid only.
                Defaults to None which will export all the grids.
        text_actor: TextActor object to add to the images. Defaults to None.
        label_images: Boolean to indicate whether to label images with the timestep
            or not. Defaults to True.
        image_width: Width of the images. Defaults to 1920.
        image_height: Height of the images. Defaults to 1088.

    Returns:
        A path to the target folder where all the images are written.
    """
    data = _validate_config(config_path)
    config_dir = pathlib.Path(config_path).parent
    path = pathlib.Path(data.path)
    if not path.is_dir():
        path = config_dir.joinpath(path).resolve().absolute()
        data.path = path.as_posix()
        if not path.is_dir():
            raise FileNotFoundError(f'No folder found at {data.path}')

    timestamp_file_path = path.joinpath(f'{timestamp_file_name}.txt')
    assert timestamp_file_path.exists(), f'File with name {timestamp_file_name}'
    ' does not exist.'

    grids_info_path = path.joinpath('grids_info.json')
    result_paths = _get_result_paths(path, grids_info_path)

    image_paths: List[str] = []
    parent_temp_folder = pathlib.Path(tempfile.mkdtemp())

    assert len(periods) == len(grid_colors), 'Number of periods and colors' \
        ' should be equal.'

    for period_count, period in enumerate(periods):
        assert period[0] < period[1], 'The start Datetime must be earlier than the end'\
            ' Datetime.'
        indexes, datetimes = _get_timestamp_indexes(timestamp_file_path, period)

        for count, index in enumerate(indexes):
            temp_folder, index_folder = _create_folders(parent_temp_folder, index)
            _copy_grids_info(grids_info_path, index_folder)
            _write_res_files(result_paths, index, index_folder)

            grid_camera_dict = _get_grid_camera_dict(data, grid_display_mode,
                                                     temp_folder, index_folder,
                                                     hbjson_path,
                                                     target_folder, index)

            config_path = _write_config(data, temp_folder, index_folder)
            model = Model.from_hbjson(hbjson_path, SensorGridOptions.Mesh)
            if label_images:
                text_actor = TextActor(text=f'{datetimes[count]}')

            image_paths += model.to_grid_images(folder=target_folder,
                                                config=config_path.as_posix(),
                                                grid_display_mode=grid_display_mode,
                                                text_actor=text_actor,
                                                image_name=f'{datetimes[count].hoy}',
                                                grid_camera_dict=grid_camera_dict,
                                                grid_filter=grid_filter,
                                                grid_color=grid_colors[period_count],
                                                sub_folder_name=f'{period_count}',
                                                image_width=image_width,
                                                image_height=image_height)

    try:
        shutil.rmtree(parent_temp_folder)
    except Exception:
        pass

    return target_folder


def _validate_periods(periods_path: str) -> Periods:
    """Validate the periods file and get it as a Periods object."""
    try:
        with open(periods_path) as fh:
            periods = json.load(fh)
    except json.decoder.JSONDecodeError:
        raise TypeError(
            'Not a valid json file.'
        )
    else:
        return Periods.parse_obj(periods)


def _extract_periods_colors(periods_path: str) -> Tuple[
        List[Tuple[DateTime, DateTime]], List[Color]
]:
    """Extract the periods and colors from the periods file.

    Args:
        periods_path: Path to the periods file.

    Returns:
        A tuple of two items:

        -   A list of DateTime objects.

        -  A list of Color objects.
    """
    periods = _validate_periods(periods_path)
    lb_periods, lb_colors = [], []

    for period in periods.periods:
        start = DateTime(period.date_time[0].month, period.date_time[0].day,
                         period.date_time[0].hour)
        end = DateTime(period.date_time[1].month, period.date_time[1].day,
                       period.date_time[1].hour)
        lb_periods.append((start, end))
        lb_colors.append(Color(*period.color))

    return lb_periods, lb_colors
