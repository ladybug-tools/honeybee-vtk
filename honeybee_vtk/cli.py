"""honeybee-vtk command line interface."""

import sys
import pathlib

import click
from click.exceptions import ClickException

from .writer import writer


@click.group()
def main():
    """Honeybee VTK commands entry point."""
    pass


@main.command('translate')
@click.argument('hbjson-file')
@click.option(
    '--name', '-n', help='Name of the output file. If not provided, the name of '
    'input HBJSON file will be used.'
)
@click.option(
    '--folder', '-f', help='Path to target folder.',
    type=click.Path(exists=False, file_okay=False, resolve_path=True, dir_okay='True'),
    default='.', show_default=True
)
@click.option(
    '--file-type', '-t', type=click.Choice(['vtk', 'xml', 'html']), default='html',
    help='Switch between VTK, XML, and HTML formats. Default is HTML.',
    show_default=True
)
@click.option(
    '--include-grids', '-ig', is_flag=True, default=False,
    help='Export grids.', show_default=True
)
@click.option(
    '--include-sensors', '-is', type=click.Choice(['vectors', 'points']),
    help='Export sensors as either arrows or color-grouped points.', show_default=True
)
@click.option(
    '--include-normals', '-in', type=click.Choice(['vectors', 'points']),
    help='Export aperture normals as either arrows or color-grouped points.',
    show_default=True
)
@click.option(
    '--show-html', '--show', '-sh', is_flag=True, default=False,
    help='Open the generated HTML file in a browser.', show_default=True
)
def translate_recipe(
        hbjson_file, name, folder, file_type, include_grids, include_sensors,
        include_normals, show_html
    ):
    """Translate a HBJSON file to several VTK, XML, or HTML file.

    The output file is either a zipped file that contains all the generated VTK/XML files
    or an HTML file.

    \b
    Args:
        hbjson-file: Path to input HBJSON file.

    """

    folder = pathlib.Path(folder)
    folder.mkdir(exist_ok=True)
    if not include_normals:
        include_normals = False
    if not include_sensors:
        include_sensors = False

    try:
        output_file = writer(
            hbjson_file, target_folder=folder, file_name=name,
            include_grids=include_grids, include_sensors=include_sensors,
            include_normals=include_normals, writer=file_type, open_html=show_html
        )
    except Exception as e:
        raise ClickException(f'Translation to VTK failed:\n{e}')
    else:
        print(f'Success: {output_file}', file=sys.stderr)
        return sys.exit(0)
