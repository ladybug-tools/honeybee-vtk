"""Unit tests for the cli module."""

import pytest
import os
from click.testing import CliRunner
from honeybee_vtk.cli import translate_recipe
from ladybug.futil import nukedir


def test_translate_recipe():
    """Test cli command."""
    runner = CliRunner()
    file_path = './tests/assets/unnamed.hbjson' 
    target_folder = './tests/target'

    # Optional arguments are deliberately capitalized or uppercased to testing
    result = runner.invoke(translate_recipe, [
        file_path, '--name', 'Model', '--folder', target_folder, '--file-type',
        'HTML', '--display-mode', 'Shaded', '--grid-options', 'MESHES'])

    assert result.exit_code == 0
    html_path = os.path.join(target_folder, 'Model.html')
    assert os.path.isfile(html_path)
    nukedir(target_folder, True)

    # Optional arguments are deliberately capitalized or uppercased to testing
    result = runner.invoke(translate_recipe, [
        file_path, '--name', 'Model', '--folder', target_folder, '--file-type',
        'VTKJS', '--display-mode', 'Shaded', '--grid-options', 'Points'])

    assert result.exit_code == 0
    vtkjs_path = os.path.join(target_folder, 'Model.vtkjs')
    assert os.path.isfile(vtkjs_path)
    nukedir(target_folder, True)