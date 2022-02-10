
import os
from click.testing import CliRunner
from honeybee_vtk.cli.export_grid import export_grid
from ladybug.futil import nukedir


def test_export_grid_images():
    """Testing command with defaults."""
    runner = CliRunner()
    file_path = r'tests/assets/gridbased.hbjson'
    target_folder = r'tests/assets/target'
    config_path = r'tests/assets/config/valid_with_grid_filter.json'

    nukedir(target_folder, True)

    result = runner.invoke(
        export_grid, [
            file_path, '--folder', target_folder, '--image-type', 'jpg',
            '--image-width', 500, '--image-height', 500,
            '--background-color', 255, 255, 255, '--grid-option', 'meshes',
            '--grid-display-mode', 'Surfacewithedges', '--config', config_path])

    assert result.exit_code == 0
    exported_file_names = os.listdir(target_folder)

    file_names = ['Daylight-Factor_TestRoom_1.jpg']
    assert all([name in file_names for name in exported_file_names])

    nukedir(target_folder, True)
