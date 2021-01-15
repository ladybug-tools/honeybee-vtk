"""Honeybee VTK command line interface."""
import sys
import pathlib

import click
from click.exceptions import ClickException

from .write import write_vtk


@click.group()
def main():
    """Honeybee VTK commands entry point."""
    pass


@main.command('translate')
@click.argument('hbjson-file')
@click.option(
    '--name', '-n', help='Name of the output .zip file. If not provided, the name of '
    'input HBJSON file will be used.'
)
@click.option(
    '--folder', '-f', help='Path to target folder.',
    type=click.Path(exists=False, file_okay=False, resolve_path=True, dir_okay='True'),
    default='.', show_default=True
)
@click.option(
    '--vtk/--xml', is_flag=True, default=True, help='Switch between a vtk file format '
    'and a xml file format. Default is vtk.', show_default=True
)
@click.option(
    '--exclude-grids', '-eg', is_flag=True, default=False,
    help='Flag to exclude exporting grids.', show_default=True
)
@click.option(
    '--exclude-vectors', '-ev', is_flag=True, default=False,
    help='Flag to exclude exporting vector lines.', show_default=True
)
def translate_recipe(hbjson_file, name, folder, vtk, exclude_grids, exclude_vectors):
    """Translate a HBJSON file to several VTK files.

    The output file is a zipped file that contains all the generated VTK files.

    \b
    Args:
        hbjson-file: Path to input HBJSON file.

    """

    folder = pathlib.Path(folder)
    folder.mkdir(exist_ok=True)
    file_type = 'vtk' if vtk else 'xml'
    include_grids = not exclude_grids
    include_vectors = not exclude_vectors

    try:
        output_file = write_vtk(
            hbjson_file, target_folder=folder, file_name=name,
            include_grids=include_grids, include_vectors=include_vectors,
            writer=file_type
        )
    except Exception as e:
        raise ClickException(f'Translation to VTK failed:\n{e}')
    else:
        print(f'Success: {output_file}', file=sys.stderr)
        return sys.exit(0)
