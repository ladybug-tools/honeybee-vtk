"""Unit test for exporting timestep images and image processing."""

import tempfile
from pathlib import Path
from ladybug.dt import DateTime
from honeybee_vtk.timestep_images import export_timestep_images
from honeybee_vtk.image_processing import write_gif, write_transparent_images
from ladybug.color import Color


def test_timestep_images_export(temp_folder):
    """Test if timestep images are exported."""
    hbjson_path = r'tests/assets/gridbased_with_timesteps/inputs/model/gridbased.hbjson'
    config_path = r'tests/assets/gridbased_with_timesteps/config.json'

    periods = [
        (DateTime(12, 21, 8), DateTime(12, 21, 9)),
        (DateTime(3, 21, 8), DateTime(3, 21, 9)),
        (DateTime(6, 21, 8), DateTime(6, 21, 9))
    ]
    grid_colors = [Color(230, 236, 15), Color(248, 174, 5), Color(249, 7, 3)]

    export_timestep_images(hbjson_path, config_path, 'sun-up-hours',
                           periods, grid_colors,
                           target_folder=temp_folder.as_posix(),
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

    gif_folder = Path(tempfile.mkdtemp())
    write_gif(temp_folder, gif_folder.as_posix())

    parent_folder_names = ('TestRoom_1_gif', 'TestRoom_2_gif')

    for item in gif_folder.rglob('*.gif'):
        assert item.parent.stem in parent_folder_names and item.stem == 'output'


def test_transparent_images_export(temp_folder):
    """Test if GIFs are being created correctly."""

    transparent_images_folder = Path(tempfile.mkdtemp())
    write_transparent_images(temp_folder, transparent_images_folder.as_posix())

    parent_folder_names = ('TestRoom_1_images', 'TestRoom_2_images')
    image_names = ('0', '1', '2')

    for item in transparent_images_folder.rglob('*.png'):
        assert item.parent.stem in parent_folder_names and item.stem in image_names
