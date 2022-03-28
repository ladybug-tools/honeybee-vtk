"""Unit test for exporting timestep images and image processing."""

import tempfile
import json
from pathlib import Path
from ladybug.dt import DateTime
from honeybee_vtk.config import TimeStepConfig, TimeStepDataConfig
from honeybee_vtk.timestep_images import export_timestep_images, write_timestep_data
from honeybee_vtk.image_processing import write_gif, write_transparent_images
from ladybug.color import Color


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

    time_step_data_json_path = write_timestep_data(
        time_step_file_path, periods_file_path, time_step_config_folder.as_posix())

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
            export_timestep_images(hbjson_path, config_path, time_step_data,
                                   target_folder=temp_folder,
                                   label_images=False)

    export_timestep_images(hbjson_path, config_path, time_step_data,
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

    parent_folder_names = ('TestRoom_1_gif', 'TestRoom_2_gif')

    for item in gif_folder.rglob('*.gif'):
        assert item.parent.stem in parent_folder_names and item.stem == 'output'


def test_transparent_images_export(temp_folder):
    """Test if GIFs are being created correctly."""

    images_folder = temp_folder.joinpath('images')

    transparent_images_folder = Path(tempfile.mkdtemp())
    write_transparent_images(images_folder.as_posix(),
                             transparent_images_folder.as_posix())

    parent_folder_names = ('TestRoom_1_images', 'TestRoom_2_images')
    image_names = ('0', '1', '2')

    for item in transparent_images_folder.rglob('*.png'):
        assert item.parent.stem in parent_folder_names and item.stem in image_names
