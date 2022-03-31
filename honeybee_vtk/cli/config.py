"""Honeybee-vtk command to write a config file to be consumed by honeybee-vtk."""

import click
import sys
import traceback
from honeybee_vtk.time_step_images import write_time_step_data


@click.group()
def config():
    """Command to write config files to be consumed by honeybee-vtk."""
    pass


@config.command('time-step-data')
@click.option(
    '--time-step-file', '-tsf', type=click.Path(exists=True), default=None,
    show_default=True, required=True, help='Path to the time step file such as,'
    ' sun-up-hours.txt.'
)
@click.option(
    '--periods-file', '-pf', type=click.Path(exists=True), default=None,
    show_default=True, required=True, help='Path to the periods file.'
)
@click.option(
    '--file-name', '-fn', type=str, default='timestep_data', show_default=True,
    help='Name of the timestep data file. Default is "timestep_data".'
)
@click.option(
    '--folder', '-f', type=click.Path(exists=False, file_okay=False, resolve_path=True,
                                      dir_okay=True),
    default='.', show_default=True, help='Path to target folder.',
)
def time_step_data(time_step_file, periods_file, folder, file_name):
    """Write a JSON file to be consumed by the "time-step-images" subcommand of the
    "export" command of honeybee-vtk.

    \b
    Args:
        time_step_file: Path to the time step file such as, sun-up-hours.txt.
        periods_file: Path to the periods file.
        folder: Path to target folder.
        file_name: Name of the timestep data file. Default is "timestep_data".
    """
    try:
        output = write_time_step_data(time_step_file, periods_file, file_name, folder)
    except Exception:
        traceback.print_exc()
        sys.exit(1)
    else:
        print(f'Success: {output}', file=sys.stderr)
        return sys.exit(0)
