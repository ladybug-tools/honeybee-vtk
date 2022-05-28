"""Function to generate images from time series data."""

import json
import pathlib
import tempfile
import shutil
import os
import vtk

from pathlib import Path
from pandas import DataFrame
from typing import List, Tuple, Dict, Union
from ladybug.dt import DateTime
from ladybug.color import Color


from .config import Config, DataConfig, Autocalculate, Periods, TimeStepConfig, \
    TimeStepDataConfig
from .model import Model, SensorGridOptions
from .vtkjs.schema import DisplayMode
from .text_actor import TextActor


def _validate_periods(periods_file_path: str) -> Periods:
    """Validate the periods file and get it as a Periods object."""
    try:
        with open(periods_file_path) as fh:
            periods = json.load(fh)
    except json.decoder.JSONDecodeError:
        raise TypeError(
            'Not a valid json file.'
        )
    else:
        return Periods.parse_obj(periods)


def _extract_periods_colors(periods_file_path: Path) -> Tuple[
        List[Tuple[DateTime, DateTime]], List[Color]
]:
    """Extract the periods and colors from the periods file.

    Args:
        periods_path: Path to the periods file.

    Returns:
        A tuple of two items:

        -   A list of tuple of Datetime objects.

        -  A list of Color objects.
    """
    periods = _validate_periods(periods_file_path)
    lb_periods, lb_colors = [], []

    for period in periods.periods:
        start = DateTime(period.date_time[0].month, period.date_time[0].day,
                         period.date_time[0].hour)
        end = DateTime(period.date_time[1].month, period.date_time[1].day,
                       period.date_time[1].hour)
        lb_periods.append((start, end))
        lb_colors.append(Color(*period.color))

    assert len(lb_periods) == len(lb_colors), 'The number of periods and colors'\
        ' must be the same.'
    return lb_periods, lb_colors


def _get_datetimes(path: Path) -> List[DateTime]:
    """Read a .txt file with time stamps and return a list of Datetime object.

    Here, time stamp can be HOY, MOY, or DOY.

    Args:
        path: Path to the .txt file.

    Returns:
        A list of Datetime objects.
    """
    with open(path, 'r') as f:
        return [DateTime.from_hoy(float(line.strip())) for line in f]


def write_time_step_data(
        time_step_file_path: str, periods_file_path: str,
        file_name: str = 'timestep_data',
        target_folder: str = '.') -> Path:
    """Create time step data to loop over.

    This function reads the time step file and the periods file to generate JSON file
    that contains data required to generate image of each time step.

    Args:
        time_step_file_path: Path to the time step file such as sun-up-hours.txt.
        periods_file_path: Path to the periods file.
        file_name: Name of the JSON file. Defaults to 'timestep_data'.
        target_folder: Path to the folder where the JSON file will be saved.
            Defaults to '.'.

    Returns
        A path to the timestep JSON file.
    """
    time_step_path = Path(time_step_file_path)
    assert time_step_path.exists(), 'Time step file does not exist.'

    periods_path = Path(periods_file_path)
    assert periods_path.exists(), 'Periods file does not exist.'

    lb_periods, lb_colors = _extract_periods_colors(periods_path)

    time_step_data = []
    for period_count, period in enumerate(lb_periods):
        assert period[0] < period[1], 'The start Datetime must be earlier than'\
            ' the end Datetime.'
        st_datetime, end_datetime = period
        time_stamp_datetimes = _get_datetimes(time_step_path)

        for count, datetime in enumerate(time_stamp_datetimes):
            if st_datetime <= datetime <= end_datetime:
                color = lb_colors[period_count]
                time_step_data.append(
                    TimeStepConfig(index=count,
                                   hoy=datetime.hoy,
                                   color=[color.r, color.g, color.b]))

    time_step_file_path = Path(f'{target_folder}/{file_name}.json')
    with open(time_step_file_path, 'w') as f:
        data = TimeStepDataConfig(time_step_data=time_step_data)
        f.write(data.json())

    return time_step_file_path


def _get_res_file_extension(path: Path, grids_info: List[dict]) -> str:
    """Get the common file extension of the result files in the folder.

    Args:
        path: Path to the folder.
        grids_info: A list of grids info objects.

    Returns:
        The common file extension of the result files in the folder.
    """

    first_grid_id: str = grids_info[0]['identifier']
    first_grid_full_id: str = grids_info[0]['full_id']
    folder = path.joinpath(first_grid_full_id).parent
    for item in list(folder.iterdir()):
        if item.stem == first_grid_id:
            return item.suffix
    else:
        raise ValueError('Failed to find the extension for result files')


def _get_result_paths(path: Path,
                      grids_info_path: Path) -> List[Path]:
    """Get file paths of the result files in the data folder.

    Args:
        path: Path to the data folder.
        grids_info_path: Path to the grids info.json file.

    Returns:
        A list of file paths to the result files such as .ill files or .res files.
    """
    try:
        with open(grids_info_path) as fh:
            grids_info = json.load(fh)
    except json.decoder.JSONDecodeError:
        raise TypeError(
            'Not a valid json file.'
        )

    res_extension = _get_res_file_extension(path, grids_info)
    return [path.joinpath(f'{grid["full_id"]}{res_extension}') for
            grid in grids_info]


def _extract_column(path: Path, index: int) -> List[int]:
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


def _write_config(data: DataConfig, target_folder: Path, data_path: Path) -> Path:
    """Write a config file to be consumed by honeybee-vtk.

    Args:
        data: A DataConfig object.
        target_folder: Path to the folder to write the config file.
        data_path: Path to folder with grids_info.json and result files.

    this function will replace the path property in the Dataconfig object with
    data_path.

    Returns:
        Path to the config file.
    """

    data.path = data_path.as_posix()
    config = Config(data=[data])

    config_path = target_folder.joinpath('config.json')
    with open(config_path, 'w') as f:
        f.write(config.json())

    return config_path


def _process_config(config_path: str) -> Tuple[DataConfig, Path, List[Path]]:
    """Process the config file.

    This function takes a path to the config file and extracts the DataConfig object
    from the config file. Additionally, based on the path property found in the
    Dataconfig, it maps a path to the grids_info.json file and also the paths to the
    actual result files such as .ill or .res files.


    Args:
        config_path: Path to the config file.

    Returns:
        A tuple of three items:

        -   A DataConfig object.

        -   Path to the grids_info.json file.

        -   List of paths to the result files.
    """
    data = _validate_config(config_path)
    config_dir = Path(config_path).parent
    path = Path(data.path)
    if not path.is_dir():
        path = config_dir.joinpath(path).resolve().absolute()
        data.path = path.as_posix()
        if not path.is_dir():
            raise FileNotFoundError(f'No folder found at {data.path}')

    grids_info_path = path.joinpath('grids_info.json')
    result_paths = _get_result_paths(path, grids_info_path)

    return data, grids_info_path, result_paths


def _create_folders(parent_temp_folder: Path,
                    index: int) -> Tuple[Path, Path]:
    """Create a temp folder and an Index folder for the current index.

    Args:
        parent_temp_folder: Path to the parent temp folder.
        index: Index of the time stamp in the time stamps file.

    Returns:
        A tuple of paths to the temp folder and the Index folder.
    """

    temp_folder = Path(tempfile.mkdtemp(dir=parent_temp_folder.as_posix()))
    index_folder = temp_folder.joinpath(str(index))
    os.mkdir(index_folder)
    return temp_folder, index_folder


def _copy_grids_info(grids_info_path: Path, index_folder: Path) -> None:
    """Copy grids_info.json to the Index folder."""
    index_grids_info_path = Path(index_folder).joinpath('grids_info.json')
    shutil.copy(grids_info_path, index_grids_info_path)


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


def _get_grid_camera_dict(
        data: DataConfig,
        grid_display_mode: DisplayMode,
        temp_folder: Path,
        index_folder: Path,
        hbjson_path: str,
        target_folder: str,
        index: int) -> Union[None, Dict[str, vtk.vtkCamera]]:
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
    if not isinstance(data.upper_threshold, Autocalculate) or\
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


def export_time_step_images(hbjson_path: str, config_path: str,
                            time_step: TimeStepConfig,
                            grid_display_mode: DisplayMode = DisplayMode.Shaded,
                            target_folder: str = '.',
                            grid_filter: Union[str, List[str]] = None,
                            full_match: bool = False,
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
        grid_filter: A list of grid identifiers or a regex pattern as a string to
                filter the grids. Defaults to None.
        full_match: A boolean to filter grids by their identifiers as full matches.
            Defaults to False.
        text_actor: TextActor object to add to the images. Defaults to None.
        label_images: Boolean to indicate whether to label images with the timestep
            or not. Defaults to True.
        image_width: Width of the images. Defaults to 1920.
        image_height: Height of the images. Defaults to 1088.

    Returns:
        A path to the target folder where all the images are written.
    """

    # TODO _process_config should not have to be called each time the function is called.
    data, grids_info_path, result_paths = _process_config(config_path)
    parent_temp_folder = Path(tempfile.mkdtemp())
    temp_folder, index_folder = _create_folders(parent_temp_folder, time_step.index)
    _copy_grids_info(grids_info_path, index_folder)

    # use full id to support sensor grids with group identifier
    grid_info = json.loads(grids_info_path.read_text())
    for info, result_path in zip(grid_info, result_paths):
        values = _extract_column(result_path, time_step.index)
        file_path = Path(index_folder).joinpath(f'{info["full_id"]}.res')
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open('w') as f:
            for val in values:
                f.write(f'{val}\n')

    grid_camera_dict = _get_grid_camera_dict(data, grid_display_mode,
                                             temp_folder, index_folder,
                                             hbjson_path,
                                             target_folder, time_step.index)

    config_path = _write_config(data, temp_folder, index_folder)
    model = Model.from_hbjson(hbjson_path, SensorGridOptions.Mesh)

    if label_images:
        text_actor = TextActor(text=f'{DateTime.from_hoy(time_step.hoy)}')
    else:
        text_actor = None

    model.to_grid_images(folder=target_folder,
                         config=config_path.as_posix(),
                         grid_display_mode=grid_display_mode,
                         text_actor=text_actor,
                         image_name=f'{time_step.hoy}',
                         grid_camera_dict=grid_camera_dict,
                         grid_filter=grid_filter,
                         full_match=full_match,
                         grid_colors=[
                             Color(time_step.color[0], time_step.color[1],
                                   time_step.color[2])
                         ],
                         image_width=image_width,
                         image_height=image_height)

    try:
        shutil.rmtree(parent_temp_folder)
    except Exception:
        pass
