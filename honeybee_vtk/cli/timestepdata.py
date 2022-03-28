"""Command to write a timestep data file to be consumed by the "timestep-images" command
in the "export" command on honeybee-vtk."""

import click
import sys
import traceback
from honeybee_vtk.timestep_images import write_timestep_data


@click.group()
def timestepdata():
    """Honeybee-vtk command to write a JSON file that contains data to generate
    images of each time step."""
    pass


@timestepdata.command('timestep-data')
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
def config(time_step_file, periods_file, folder, file_name):
    """Write a JSON file to be consumed by the "timestep-images" subcommand of the
    "export" command of honeybee-vtk.

    \b
    Args:
        time_step_file: Path to the time step file such as, sun-up-hours.txt.
        periods_file: Path to the periods file.
        folder: Path to target folder.
        file_name: Name of the timestep data file. Default is "timestep_data".
    """
    try:
        output = write_timestep_data(time_step_file, periods_file, file_name, folder)
    except Exception:
        traceback.print_exc()
        sys.exit(1)
    else:
        print(f'Success: {output}', file=sys.stderr)
        return sys.exit(0)
