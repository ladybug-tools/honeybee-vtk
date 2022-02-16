
import os
from click.testing import CliRunner
from honeybee_vtk.cli.export import export
from ladybug.futil import nukedir


def test_export_images():
    """Test exporting images for the whole model."""
    runner = CliRunner()
    file_path = r'tests/assets/gridbased.hbjson'
    target_folder = r'tests/assets/target'
    view_file = r'tests/assets/view.vf'
    view_file_1 = r'tests/assets/view1.vf'
    config_path = r'tests/assets/config/valid.json'

    nukedir(target_folder, True)

    result = runner.invoke(
        export, [
            file_path, '--folder', target_folder, '--image-type', 'PNG',
            '--image-width', 500, '--image-height', 500,
            '--background-color', 255, 255, 255, '--grid-options', 'Meshes',
            '--model-display-mode', 'Shaded', '--grid-display-mode', 'SurfaceWithEdges',
            '--view', view_file, '--view', view_file_1, '--config', config_path])

    assert result.exit_code == 0
    exported_file_names = os.listdir(target_folder)
    file_names = ['Back.png', 'Bottom.png', 'Front.png',
                  'Left.png', 'Right.png', 'Top.png', 'view.png', 'view1.png']
    assert all([name in file_names for name in exported_file_names])

    nukedir(target_folder, True)


def test_export_grid_images():
    """Test exporting images for the grids."""
    runner = CliRunner()
    file_path = r'tests/assets/gridbased.hbjson'
    target_folder = r'tests/assets/target'
    config_path = r'tests/assets/config/valid.json'

    nukedir(target_folder, True)

    result = runner.invoke(
        export, [
            file_path, '--folder', target_folder, '--image-type', 'PNG',
            '--image-width', 500, '--image-height', 500,
            '--background-color', 255, 255, 255, '--grid-options', 'Meshes',
            '--model-display-mode', 'Shaded', '--grid-display-mode', 'SurfaceWithEdges',
            '--config', config_path, '--grid', '--grid-filter', 'TestRoom_1', '--text',
            'Test Room', '--text-height', 25, '--text-color', 51, 0, 0, '--text-position',
            0.5, 0.5, '--text-bold'])

    assert result.exit_code == 0
    exported_file_names = os.listdir(target_folder)
    file_names = ['Daylight-Factor_TestRoom_1.png', 'UDI_TestRoom_1.png']
    assert all([name in file_names for name in exported_file_names])

    nukedir(target_folder, True)
