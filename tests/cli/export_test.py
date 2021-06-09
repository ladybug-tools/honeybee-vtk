import traceback
import pytest
import os
from traceback import TracebackException
from click.testing import CliRunner
from honeybee_vtk.cli.export import export
from ladybug.futil import nukedir


# def test_export_image():
#     """Testing command with defaults."""
#     runner = CliRunner()
#     file_path = './tests/assets/gridbased.hbjson'
#     target_folder = './tests/assets/target'
#     view_file = './tests/assets/view.vf'
#     view_file_1 = './tests/assets/view1.vf'
#     config_path = './tests/assets/config/valid.json'

#     result = runner.invoke(
#         export, [
#             file_path, '--folder', target_folder, '--name', 'Model', '--image-type',
#             'PNG', '--image-width', 200, '--image-height', 500,
#             '--background-color', 255, 255, 255, '--grid-options', 'Meshes',
#             '--display-mode-model', 'Shaded', '--display-mode-grid', 'SurfaceWithEdges',
#             '--view', view_file, '--view', view_file_1, '--data-config', config_path])

#     assert result.exit_code == 0
#     images_path = os.listdir(target_folder)
#     assert all([item[:5] == 'Model' and item[-4:] == '.png' for item in images_path])
#     nukedir(target_folder, True)
