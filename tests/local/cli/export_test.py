
import os
from pathlib import Path
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
            'model-images',
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


def test_export_images_with_radial_grid():
    """Test exporting images for the model with radial-grids."""

    runner = CliRunner()
    file_path = r'tests/assets/radial_grid/hb_sample_model_grid.hbjson'
    target_folder = r'tests/assets/target'
    config_path = r'tests/assets/radial_grid/config.json'

    nukedir(target_folder, True)

    result = runner.invoke(
        export, [
            'model-images',
            file_path, '--folder', target_folder, '--grid-options', 'radial-grid',
            '-ta', 30, '-tr', 0.6, '--config', config_path, '-mdm', 'wireframe'])

    assert result.exit_code == 0
    exported_file_names = os.listdir(target_folder)
    file_names = ['45_degrees.jpg', '135_degrees.jpg', '225_degrees.jpg',
                  '315_degrees.jpg', 'plan.jpg']
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
            'grid-images',
            file_path, '--folder', target_folder, '--image-type', 'PNG',
            '--image-width', 500, '--image-height', 500,
            '--background-color', 255, 255, 255, '--grid-options', 'Meshes',
            '--grid-display-mode', 'SurfaceWithEdges',
            '--config', config_path, '--grid-filter', 'TestRoom_1',
            '--text-content', 'Test Room', '--text-height', 25,
            '--text-color', 51, 0, 0, '--text-position', 0.5, 0.5, '--text-bold'])

    assert result.exit_code == 0
    exported_file_names = os.listdir(f'{target_folder}/TestRoom_1')
    file_names = ['Daylight-Factor_TestRoom_1.png', 'UDI_TestRoom_1.png']
    assert all([name in file_names for name in exported_file_names])

    nukedir(target_folder, True)


def test_export_timestep_images():
    """"Test exporting a gif for the timesteps."""
    runner = CliRunner()
    target_folder = r'tests/assets/target'
    file_path = r'tests/assets/gridbased_with_timesteps/inputs/model/gridbased.hbjson'
    config_path = r'tests/assets/gridbased_with_timesteps/config.json'
    time_step_path = r'tests/assets/gridbased_with_timesteps/time_steps.json'

    nukedir(target_folder, True)

    result = runner.invoke(
        export, [
            'time-step-images',
            file_path, '--config', config_path, '--time-step-file', time_step_path,
            '--folder', target_folder, '--grid-filter', 'TestRoom_1'])

    assert result.exit_code == 0

    target_folder = Path(target_folder)

    file_names = (
        '1904.5_sun-up-hours_TestRoom_1',
        '4112.5_sun-up-hours_TestRoom_1',
        '8504.5_sun-up-hours_TestRoom_1'
    )

    for file_path in target_folder.rglob('*.png'):
        assert file_path.parent.stem == 'TestRoom_1' and file_path.stem in file_names

    nukedir(target_folder, True)
