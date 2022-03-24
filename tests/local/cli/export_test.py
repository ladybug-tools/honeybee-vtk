
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
            '--config', config_path, '--selection', 'grid', '--grid-filter', 'TestRoom_1',
            '--text-content', 'Test Room', '--text-height', 25, '--text-color', 51, 0, 0,
            '--text-position', 0.5, 0.5, '--text-bold'])

    assert result.exit_code == 0
    exported_file_names = os.listdir(f'{target_folder}/TestRoom_1')
    file_names = ['Daylight-Factor_TestRoom_1.png', 'UDI_TestRoom_1.png']
    assert all([name in file_names for name in exported_file_names])

    nukedir(target_folder, True)


def test_export_timestep_gif():
    """"Test exporting a gif for the timesteps."""
    runner = CliRunner()
    target_folder = r'tests/assets/target'
    file_path = r'tests/assets/gridbased_with_timesteps/inputs/model/gridbased.hbjson'
    config_path = r'tests/assets/gridbased_with_timesteps/config.json'
    peridos_path = r'tests/assets/gridbased_with_timesteps/periods.json'

    nukedir(target_folder, True)

    result = runner.invoke(
        export, [
            file_path, '--folder', target_folder, '-go', 'meshes', '--config',
            config_path, '-sel', 'timesteps', '-tfn', 'sun-up-hours', '-pf',
            peridos_path])

    assert result.exit_code == 0

    parent_folder_names = ('TestRoom_1_gif', 'TestRoom_2_gif')

    target_folder = Path(target_folder)
    for item in target_folder.rglob('*.gif'):
        assert item.parent.stem in parent_folder_names and item.stem == 'output'

    nukedir(target_folder, True)


def test_export_timestep_gif_and_images():
    """"Test exporting a gif and transparent images for the timesteps."""
    runner = CliRunner()
    target_folder = r'tests/assets/target'
    file_path = r'tests/assets/gridbased_with_timesteps/inputs/model/gridbased.hbjson'
    config_path = r'tests/assets/gridbased_with_timesteps/config.json'
    peridos_path = r'tests/assets/gridbased_with_timesteps/periods.json'

    nukedir(target_folder, True)

    result = runner.invoke(
        export, [
            file_path, '--folder', target_folder, '-go', 'meshes', '--config',
            config_path, '-sel', 'timesteps', '-tfn', 'sun-up-hours', '-pf',
            peridos_path, '--transparent-images'])

    assert result.exit_code == 0

    gif_parent_folder_names = ('TestRoom_1_gif', 'TestRoom_2_gif')

    target_folder = Path(target_folder)
    for item in target_folder.rglob('*.gif'):
        assert item.parent.stem in gif_parent_folder_names and item.stem == 'output'

    images_parent_folder_names = ('TestRoom_1_images', 'TestRoom_2_images')
    image_names = ('0', '1', '2')

    for item in target_folder.rglob('*.png'):
        assert item.parent.stem in images_parent_folder_names and \
            item.stem in image_names

    nukedir(target_folder, True)
