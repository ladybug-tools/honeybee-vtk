"""honeybee-vtk command line interface."""

import sys
import pathlib
import traceback
import click

from honeybee_vtk.model import Model
from honeybee_vtk.vtkjs.schema import SensorGridOptions, DisplayMode
from honeybee_vtk.types import VTKWriters


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
    '--file-type', '-ft', type=click.Choice(['html', 'vtkjs', 'vtp', 'vtk'],
                                            case_sensitive=False), default='html',
    help='Switch between html and vtkjs formats', show_default=True
)
@click.option(
    '--model-display-mode', '-mdm',
    type=click.Choice(['shaded', 'surface', 'surfacewithedges', 'wireframe', 'points'],
                      case_sensitive=False),
    default='shaded', help='Set display mode for the model.', show_default=True
)
@click.option(
    '--grid-display-mode', '-gdm',
    type=click.Choice(['shaded', 'surface', 'surfacewithedges', 'wireframe', 'points'],
                      case_sensitive=False),
    default='shaded', help='Set display mode for the grid.', show_default=True
)
@click.option(
    '--grid-options', '-go',
    type=click.Choice(['ignore', 'points', 'meshes'], case_sensitive=False),
    default='ignore', help='Export sensor grids as either points or meshes.',
    show_default=True,
)
@click.option(
    '--show-html', '--show', '-sh', is_flag=True, default=False,
    help='Open the generated HTML file in a browser.', show_default=True
)
@click.option(
    '--config', '-cf', help='File Path to the config json file which can be used to'
    ' mount simulation data on HBJSON.', type=click.Path(exists=True), default=None,
    show_default=True
)
@click.option(
    '--validate-data', '-vd', is_flag=True, default=False,
    help='Validate simulation data before loading on the model. This is recommended'
    ' when using this command locally.', show_default=True
)
def translate(
        hbjson_file, name, folder, file_type, model_display_mode, grid_display_mode,
        grid_options, show_html,
        config, validate_data):
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

    # Set display style
    if model_display_mode == 'shaded':
        model_display_mode = DisplayMode.Shaded
    elif model_display_mode == 'surface':
        model_display_mode = DisplayMode.Surface
    elif model_display_mode == 'surfacewithedges':
        model_display_mode = DisplayMode.SurfaceWithEdges
    elif model_display_mode == 'wireframe':
        model_display_mode = DisplayMode.Wireframe
    elif model_display_mode == 'points':
        model_display_mode = DisplayMode.Points

    if grid_display_mode == 'shaded':
        grid_display_mode = DisplayMode.Shaded
    elif grid_display_mode == 'surface':
        grid_display_mode = DisplayMode.Surface
    elif grid_display_mode == 'surfacewithedges':
        grid_display_mode = DisplayMode.SurfaceWithEdges
    elif grid_display_mode == 'wireframe':
        grid_display_mode = DisplayMode.Wireframe
    elif grid_display_mode == 'points':
        grid_display_mode = DisplayMode.Points

    try:
        model = Model.from_hbjson(hbjson=hbjson_file, load_grids=grid_options)

        if file_type.lower() == 'html':
            output = model.to_html(folder=folder, name=name,
                                   show=show_html, config=config,
                                   model_display_mode=model_display_mode,
                                   grid_display_mode=grid_display_mode,
                                   validation=validate_data)
        elif file_type.lower() == 'vtkjs':
            output = model.to_vtkjs(folder=folder, name=name,
                                    config=config,
                                    model_display_mode=model_display_mode,
                                    grid_display_mode=grid_display_mode,
                                    validation=validate_data)
        elif file_type.lower() == 'vtk':
            output = model.to_files(folder=folder, name=name,
                                    writer=VTKWriters.legacy, config=config,
                                    model_display_mode=model_display_mode,
                                    grid_display_mode=grid_display_mode,
                                    validation=validate_data)
        elif file_type.lower() == 'vtp':
            output = model.to_files(folder=folder, name=name,
                                    writer=VTKWriters.binary, config=config,
                                    model_display_mode=model_display_mode,
                                    grid_display_mode=grid_display_mode,
                                    validation=validate_data)

    except Exception as e:
        traceback.print_exc()
        sys.exit(1)
    else:
        print(f'Success: {output}', file=sys.stderr)
        return sys.exit(0)
