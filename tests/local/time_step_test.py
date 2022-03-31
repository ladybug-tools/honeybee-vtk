"""Unit test for exporting timestep images and image processing."""

import tempfile
import json
from pathlib import Path

from honeybee_vtk.config import TimeStepDataConfig
from honeybee_vtk.time_step_images import export_time_step_images, write_time_step_data
from honeybee_vtk.image_processing import write_gif, write_transparent_images


def test_timestep_images_export(temp_folder):
    """Test if timestep images are exported."""
    hbjson_path = r'tests/assets/gridbased_with_timesteps/inputs/model/gridbased.hbjson'
    config_path = r'tests/assets/gridbased_with_timesteps/config.json'
    time_step_file_path = r'tests/assets/gridbased_with_timesteps/outputs/direct-sun-hours/sun-up-hours.txt'
    periods_file_path = r'tests/assets/gridbased_with_timesteps/periods.json'

    time_step_config_folder = temp_folder.joinpath('time_step_data')
    time_step_config_folder.mkdir()
    images_folder = temp_folder.joinpath('images')
    images_folder.mkdir()

    time_step_data_json_path = write_time_step_data(
        time_step_file_path, periods_file_path,
        target_folder=time_step_config_folder.as_posix())

    try:
        with open(time_step_data_json_path) as fh:
            config = json.load(fh)
    except json.decoder.JSONDecodeError:
        raise TypeError(
            'Not a valid json file.'
        )
    else:
        data = TimeStepDataConfig.parse_obj(config)
        for time_step_data in data.time_step_data:
            export_time_step_images(hbjson_path, config_path, time_step_data,
                                    target_folder=images_folder.as_posix(),
                                    label_images=False)

    assert len(list(temp_folder.iterdir())) > 0

    image_names = (
        '8504.5_sun-up-hours_TestRoom_1',
        '1904.5_sun-up-hours_TestRoom_1',
        '4112.5_sun-up-hours_TestRoom_1',
        '8504.5_sun-up-hours_TestRoom_2',
        '1904.5_sun-up-hours_TestRoom_2',
        '4112.5_sun-up-hours_TestRoom_2',
    )

    assert all([item.stem in image_names for item in temp_folder.rglob('*.png')])


def test_gif_export(temp_folder):
    """Test if GIFs are being created correctly."""

    images_folder = temp_folder.joinpath('images')

    gif_folder = Path(tempfile.mkdtemp())
    write_gif(images_folder.as_posix(), gif_folder.as_posix())

    gif_names = ('TestRoom_1', 'TestRoom_2')

    for file_path in gif_folder.rglob('*.gif'):
        assert file_path.stem in gif_names


def test_transparent_images_export(temp_folder):
    """Test if GIFs are being created correctly."""

    images_folder = temp_folder.joinpath('images')

    transparent_images_folder = Path(tempfile.mkdtemp())
    write_transparent_images(images_folder.as_posix(),
                             transparent_images_folder.as_posix())

    parent_folder_names = ('TestRoom_1_trans_images', 'TestRoom_2_trans_images')
    image_names = ('0', '1', '2')

    for file_path in transparent_images_folder.rglob('*.png'):
        assert file_path.parent.stem in parent_folder_names and \
            file_path.stem in image_names
