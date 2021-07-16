import traceback
import pytest
import os
from traceback import TracebackException
from click.testing import CliRunner
from honeybee_vtk.cli.export import export
from ladybug.futil import nukedir


def test_export_image():
    """Testing command with defaults."""
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
