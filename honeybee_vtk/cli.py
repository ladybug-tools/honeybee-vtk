"""Honeybee VTK command line interface."""
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
    '--file-type', type=click.Choice(['vtk', 'xml', 'html']), is_flag=True, default=True,
    help='Switch between VTK, XML, and HTML formats. Default is HTML.',
    show_default=True
)
@click.option(
    '--exclude-grids', '-eg', is_flag=True, default=False,
    help='Exclude exporting grids.', show_default=True
)
@click.option(
    '--exclude-vectors', '-ev', is_flag=True, default=False,
    help='Exclude exporting vector lines.', show_default=True
)
@click.option(
    '--open-html', '-oh', is_flag=True, default=True,
    help='Stop from the generated HTML open up in a browser', show_default=True
)
def translate_recipe(
    hbjson_file, name, folder, file_type, exclude_grids, exclude_vectors, open_html):
    """Translate a HBJSON file to several VTK, XML, or HTML file.

    The output file is a zipped file that contains all the generated VTK files.

    \b
    Args:
        hbjson-file: Path to input HBJSON file.

    """

    folder = pathlib.Path(folder)
    folder.mkdir(exist_ok=True)
    include_grids = not exclude_grids
    include_vectors = not exclude_vectors

    try:
        output_file = writer(
            hbjson_file, target_folder=folder, file_name=name,
            include_grids=include_grids, include_vectors=include_vectors,
            writer=file_type, open_html=open_html
        )
    except Exception as e:
        raise ClickException(f'Translation to VTK failed:\n{e}')
    else:
        print(f'Success: {output_file}', file=sys.stderr)
        return sys.exit(0)
