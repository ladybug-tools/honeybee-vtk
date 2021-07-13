"""honeybee-vtk command line interface."""

import sys
import pathlib
import traceback

import click
from click.exceptions import ClickException

from honeybee_vtk.model import Model
from honeybee_vtk.vtkjs.schema import SensorGridOptions, DisplayMode
from honeybee_vtk.config import load_config
from honeybee_vtk.scene import Scene
from honeybee_vtk.camera import Camera
from honeybee_vtk.actor import Actor
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
@click.option(
    '--config', '-cf', help='File Path to the config json file which can be used to'
    ' mount simulation data on HBJSON.', type=click.Path(exists=True), default=None,
    show_default=True
)
def translate(
        hbjson_file, name, folder, file_type, display_mode, grid_options, show_html,
        config):
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

        # load data
        if config:
            scene = Scene()
            actors = Actor.from_model(model)
            bounds = Actor.get_bounds(actors)
            centroid = Actor.get_centroid(actors)
            cameras = Camera.aerial_cameras(bounds=bounds, centroid=centroid)
            scene.add_actors(actors)
            scene.add_cameras(cameras)
            model = load_config(config, model, scene)

        # Set file type

        if file_type.lower() == 'html':
            output = model.to_html(folder=folder, name=name, show=show_html)
        elif file_type.lower() == 'vtkjs':
            output = model.to_vtkjs(folder=folder, name=name)
        elif file_type.lower() == 'vtk':
            output = model.to_files(folder=folder, name=name,
                                    writer=VTKWriters.legacy)
        elif file_type.lower() == 'vtp':
            output = model.to_files(folder=folder, name=name,
                                    writer=VTKWriters.binary)

    except Exception as e:
        traceback.print_exc()
        sys.exit(1)
    else:
        print(f'Success: {output}', file=sys.stderr)
        return sys.exit(0)
