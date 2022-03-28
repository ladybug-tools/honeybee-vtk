"""Unit test for the postprocess cli module."""


from pathlib import Path
from click.testing import CliRunner
from honeybee_vtk.cli.post_process import postprocess
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
        postprocess, [
            'gif', images_folder, '--folder', target_folder,
            '--gradient-transparency', '--gif-duration', 1000,
            '--gif-loop-count', 0, '--gif-linger-last-frame', 3])

    assert result.exit_code == 0

    gif_names = ('TestRoom_1', 'TestRoom_2')
    for file_path in target_folder.rglob('*.gif'):
        print(file_path)
        assert file_path.stem in gif_names

    nukedir(target_folder, True)
