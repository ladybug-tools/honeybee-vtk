"""Unit test for the postprocess cli module."""


from pathlib import Path
from click.testing import CliRunner
from honeybee_vtk.cli.post_process import post_process
from ladybug.futil import nukedir


def test_gif():
    """Test cli command."""
    runner = CliRunner()
    images_folder = r'tests/assets/time_step_images'
    target_folder = r'tests/target'

    target_folder = Path(target_folder)
    if not target_folder.exists():
        target_folder.mkdir()

    result = runner.invoke(
        post_process, [
            'gif', images_folder, '--folder', target_folder,
            '--gradient-transparency', '--duration', 1000,
            '--loop-count', 0, '--linger-last-frame', 3])

    assert result.exit_code == 0

    gif_names = ('TestRoom_1', 'TestRoom_2')
    for file_path in target_folder.rglob('*.gif'):
        assert file_path.stem in gif_names

    nukedir(target_folder, True)


def test_transparent_images():
    """Test cli command."""
    runner = CliRunner()
    images_folder = r'tests/assets/time_step_images'
    target_folder = r'tests/target'

    target_folder = Path(target_folder)
    if not target_folder.exists():
        target_folder.mkdir()

    result = runner.invoke(
        post_process, [
            'transparent-images', images_folder, '--folder', target_folder,
            '--transparency', 0.6])

    assert result.exit_code == 0

    parent_folder_names = ('TestRoom_1_trans_images', 'TestRoom_2_trans_images')
    file_names = ('0', '1', '2')
    for file_path in target_folder.rglob('*.png'):
        assert file_path.parent.stem in parent_folder_names and\
            file_path.stem in file_names

    nukedir(target_folder, True)
