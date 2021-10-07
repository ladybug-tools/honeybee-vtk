"""Unit tests for the config cli module."""

import pytest
import os
from click.testing import CliRunner
from honeybee_vtk.cli.config import config
from ladybug.futil import nukedir

runner = CliRunner()
df = r'tests/assets/df_results'
udi = r'tests/assets/udi_results'
input_file = r'tests/assets/input/input.json'
input_file_id_short = r'tests/assets/input/input_id_short.json'
input_file_unit_short = r'tests/assets/input/input_unit_short.json'
target_folder = r'tests/target'


def test_generation():
    """Test if a config file is successfully generated."""
    result = runner.invoke(config, [input_file, '--folder-path', target_folder])

    assert result.exit_code == 0
    json_path = os.path.join(target_folder, 'config.json')
    assert os.path.isfile(json_path)
    nukedir(target_folder, True)


def test_config_name():
    """Test if file name is being applied."""
    result = runner.invoke(
        config, [input_file, '--folder-path', target_folder, '--name', 'test'])

    assert result.exit_code == 0
    json_path = os.path.join(target_folder, 'test.json')
    assert os.path.isfile(json_path)
    nukedir(target_folder, True)


def test_length_of_id():
    """Test if the number of values provided to options match the number of
    result paths. In this unit test, only one value is provided to --id instead of two."""
    result = runner.invoke(
        config, [input_file_id_short, '--folder-path', target_folder, '--name', 'test'])

    assert not result.exit_code == 0


def test_length_of_unit():
    """Test if the number of values provided to options match the number of
    result paths. In this unit test, only one value is provided to --unit instead of two."""
    result = runner.invoke(
        config, [input_file_unit_short, '--folder-path', target_folder, '--name', 'test'])

    assert not result.exit_code == 0
