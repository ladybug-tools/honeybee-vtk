"""honeybee-vtk command line interface."""

import sys
import pathlib

import click
from click.exceptions import ClickException

from honeybee_vtk.model import Model
from honeybee_vtk.vtkjs.schema import SensorGridOptions, DisplayMode

@click.group()
def translate():
    """Honeybee VTK commands entry point."""
    pass


@translate.command('translate')
@click.argument('hbjson-file')
@click.option(
    '--name', '-n', help='Name of the output file.', default="model", show_default=True
)
@click.option(
    '--folder', '-f', help='Path to target folder.',
    type=click.Path(exists=False, file_okay=False, resolve_path=True,
    dir_okay='True'), default='.', show_default=True
)
@click.option(
    '--file-type', '-ft', type=click.Choice(['html', 'vtkjs'], case_sensitive=False),
    default='html', help='Switch between html and vtkjs formats', show_default=True
)
@click.option(
    '--display-mode', '-dm', type=click.Choice(['shaded', 'surface',
    'surfacewithedges', 'wireframe', 'points'], case_sensitive=False),
    default='shaded', help='Set display mode for the model.', show_default=True
)
@click.option(
    '--grid-options', '-go', type=click.Choice(['ignore', 'points', 'meshes'],
    case_sensitive=False), default='ignore', help='Export sensor grids as either'
    ' points or meshes.', show_default=True,
)
@click.option(
    '--show-html', '--show', '-sh', is_flag=True, default=False,
    help='Open the generated HTML file in a browser.', show_default=True
)
def translate(
        hbjson_file, name, folder, file_type, display_mode, grid_options, show_html):
    """Translate a HBJSON file to an HTML or a vtkjs file.

    \b
    Args:
        hbjson-file: Path to an HBJSON file.

    """
    folder = pathlib.Path(folder)
    folder.mkdir(exist_ok=True)

    # Set Sensor grids
    if grid_options == 'ignore':
        grid_options = SensorGridOptions.Ignore
    elif grid_options == 'points':
        grid_options = SensorGridOptions.Sensors
    elif grid_options == 'meshes':
        grid_options = SensorGridOptions.Mesh

    try:
        model = Model.from_hbjson(hbjson=hbjson_file, load_grids=grid_options)

        # Set display style
        if display_mode == 'shaded':
            model.update_display_mode(DisplayMode.Shaded)
        elif display_mode == 'surface':
            model.update_display_mode(DisplayMode.Surface)
        elif display_mode == 'surfacewithedges':
            model.update_display_mode(DisplayMode.SurfaceWithEdges)
        elif display_mode == 'wireframe':
            model.update_display_mode(DisplayMode.Wireframe)
        elif display_mode == 'points':
            model.update_display_mode(DisplayMode.Points)

        # Set file type
        if file_type == 'html':
            output = model.to_html(folder=folder, name=name, show=show_html)
        else:
            output = model.to_vtkjs(folder=folder, name=name)
        print(output)
    except Exception as e:
        raise ClickException(f'Translation failed:\n{e}')
    else:
        print(f'Success: {output}', file=sys.stderr)
        return sys.exit(0)


