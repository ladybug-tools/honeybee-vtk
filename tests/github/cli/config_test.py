"""Unit tests for the config cli module."""

from pathlib import Path
from click.testing import CliRunner
from honeybee_vtk.cli.config import config
from ladybug.futil import nukedir


def test_time_step_data():
    """Test cli command."""
    runner = CliRunner()
    time_step_file_path = r'tests/assets/gridbased_with_timesteps/outputs/direct-sun-hours/sun-up-hours.txt'
    periods_file_path = r'tests/assets/gridbased_with_timesteps/periods.json'
    target_folder = r'tests/target'

    target_folder = Path(target_folder)
    if not target_folder.exists():
        target_folder.mkdir()

    result = runner.invoke(
        config, [
            'time-step-data',
            '--time-step-file', time_step_file_path,
            '--periods-file', periods_file_path, '--file-name', 'timestep_data',
            '--folder', target_folder])

    assert result.exit_code == 0

    timestep_data_file = Path(target_folder).joinpath('timestep_data.json')
    assert timestep_data_file.exists()

    nukedir(target_folder, True)
