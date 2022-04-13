"""Unit tests for the cli module."""

import pytest
import os
from click.testing import CliRunner
from honeybee_vtk.cli.translate import translate
from ladybug.futil import nukedir


def test_translate():
    """Test cli command."""
    runner = CliRunner()
    file_path = r'tests/assets/unnamed.hbjson'
    target_folder = r'tests/target'

    # Optional arguments are deliberately capitalized or uppercased for testing
    result = runner.invoke(translate, [
        file_path, '--name', 'Model', '--folder', target_folder, '--file-type',
        'HTML', '--model-display-mode', 'Shaded', '--grid-options', 'MESHES'])

    assert result.exit_code == 0
    html_path = os.path.join(target_folder, 'Model.html')
    assert os.path.isfile(html_path)
    nukedir(target_folder, True)

    # Optional arguments are deliberately capitalized or uppercased for testing
    result = runner.invoke(translate, [
        file_path, '--name', 'Model', '--folder', target_folder, '--file-type',
        'VTKJS', '--model-display-mode', 'Shaded', '--grid-options', 'Points'])

    assert result.exit_code == 0
    vtkjs_path = os.path.join(target_folder, 'Model.vtkjs')
    assert os.path.isfile(vtkjs_path)
    nukedir(target_folder, True)

    # Optional arguments are deliberately capitalized or uppercased for testing
    result = runner.invoke(translate, [
        file_path, '--name', 'Model', '--folder', target_folder, '--file-type',
        'VTK', '--model-display-mode', 'Shaded', '--grid-options', 'Points'])

    assert result.exit_code == 0
    vtkjs_path = os.path.join(target_folder, 'Model.zip')
    assert os.path.isfile(vtkjs_path)
    nukedir(target_folder, True)

    # Optional arguments are deliberately capitalized or uppercased for testing
    result = runner.invoke(translate, [
        file_path, '--name', 'Model', '--folder', target_folder, '--file-type',
        'VTP', '--model-display-mode', 'Shaded', '-gdm', 'wireframe', '--grid-options',
        'Meshes'])

    assert result.exit_code == 0
    vtkjs_path = os.path.join(target_folder, 'Model.zip')
    assert os.path.isfile(vtkjs_path)
    nukedir(target_folder, True)


def test_translate_with_config():
    """Test translating to vtkjs with config."""
    runner = CliRunner()
    file_path = r'tests/assets/gridbased.hbjson'
    json_path = r'tests/assets/config/valid.json'
    target_folder = r'tests/target'

    # Optional arguments are deliberately capitalized or uppercased for testing
    result = runner.invoke(translate, [
        file_path, '--name', 'Model', '--folder', target_folder, '--file-type',
        'vtkjs', '--model-display-mode', 'Shaded', '--grid-display-mode', 'points',
        '--grid-options', 'MESHES', '--config',
        json_path])

    assert result.exit_code == 0
    html_path = os.path.join(target_folder, 'Model.vtkjs')
    assert os.path.isfile(html_path)
    nukedir(target_folder, True)


def test_translate_raidal_grid():
    """Test translating a model with radial-grid added by honeybee-vtk."""
    runner = CliRunner()
    file_path = r'tests/assets/radial_grid/hb_sample_model_grid.hbjson'
    target_folder = r'tests/assets/target'
    config_path = r'tests/assets/radial_grid/config.json'

    result = runner.invoke(translate, [
        file_path, '--name', 'Model', '--folder', target_folder, '--grid-options',
        'radial-grid', '-ta', 30, '-tr', 0.6, '--config', config_path])

    assert result.exit_code == 0
    html_path = os.path.join(target_folder, 'Model.html')
    assert os.path.isfile(html_path)
    nukedir(target_folder, True)
