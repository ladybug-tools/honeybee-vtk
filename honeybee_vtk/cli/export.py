

import pathlib
import sys
import click
from click.exceptions import ClickException

from honeybee_vtk.actor import Actor
from honeybee_vtk.scene import Scene
from honeybee_vtk.camera import Camera
from honeybee_vtk.model import Model
from honeybee_vtk.vtkjs.schema import SensorGridOptions, DisplayMode
from honeybee_vtk.types import ImageTypes


@click.group()
def export():
    """Honeybee VTK commands entry point."""
    pass

@export.command('export-images')
@click.argument('hbjson-file')
@click.option(
    '--name', '-n', help='Name of image files.', default="Camera", show_default=True
)
@click.option(
    '--folder', '-f', help='Path to target folder.',
    type=click.Path(exists=False, file_okay=False, resolve_path=True,
    dir_okay=True), default='.', show_default=True
)
@click.option(
    '--image-type', '-it', type=click.Choice(['png', 'jpg', 'ps', 'tiff', 'bmp', 'pnm'],
    case_sensitive=False), default='jpg',
    help='choose the type of image file.', show_default=True
)
@click.option(
    '--image-width', '-iw', type=int, default=2000, help='Width of image in pixels.',
    show_default=True
)
@click.option(
    '--image-height', '-ih', type=int, default=2000, help='Height of image in pixels.',
    show_default=True
)
@click.option(
    '--background-color', '-bc', type=(int, int, int), default=(255, 255, 255),
    help='background color for images', show_default=True
)
@click.option(
    '--display-mode-model', '-dmm', type=click.Choice(['shaded', 'surface',
    'surfacewithedges', 'wireframe', 'points'], case_sensitive=False),
    default='shaded', help='Set display mode for the model.', show_default=True
)
@click.option(
    '--grid-options', '-go', type=click.Choice(['ignore', 'points', 'meshes'],
    case_sensitive=False), default='ignore', help='Export sensor grids as either'
    ' points or meshes.', show_default=True,
)
@click.option(
    '--display-mode-grid', '-dmg', type=click.Choice(['shaded', 'surface',
    'surfacewithedges', 'wireframe', 'points'], case_sensitive=False),
    default='shaded', help='Set display mode for the Sensorgrids.', show_default=True
)
def export(
        hbjson_file, name, folder, image_type, image_width, image_height,
        background_color, display_mode_model, grid_options, display_mode_grid):
    """Export images from radiance views in a HBJSON file.

    \b
    Args:
        hbjson-file: Path to an HBJSON file.

    """
    folder = pathlib.Path(folder)
    folder.mkdir(exist_ok=True)

    # Set image types
    if image_type == 'png':
        image_type = ImageTypes.png
    elif image_type == 'jpg':
        image_type = ImageTypes.jpg
    elif image_type == 'ps':
        image_type == ImageTypes.ps
    elif image_type == 'tiff':
        image_type == ImageTypes.tiff
    elif image_type == 'ps':
        image_type == ImageTypes.ps
    elif image_type == 'pnm':
        image_type == ImageTypes.pnm

    # Set Sensor grids
    if grid_options == 'ignore':
        grid_options = SensorGridOptions.Ignore
    elif grid_options == 'points':
        grid_options = SensorGridOptions.Sensors
    elif grid_options == 'meshes':
        grid_options = SensorGridOptions.Mesh

    try:
        model = Model.from_hbjson(hbjson=hbjson_file, load_grids=grid_options)

        # Set model's display mode
        if display_mode_model == 'shaded':
            model.update_display_mode(DisplayMode.Shaded)
        elif display_mode_model == 'surface':
            model.update_display_mode(DisplayMode.Surface)
        elif display_mode_model == 'surfacewithedges':
            model.update_display_mode(DisplayMode.SurfaceWithEdges)
        elif display_mode_model == 'wireframe':
            model.update_display_mode(DisplayMode.Wireframe)
        elif display_mode_model == 'points':
            model.update_display_mode(DisplayMode.Points)

        # Set model's grid's display mode
        if display_mode_grid == 'shaded':
            model.sensor_grids.display_mode = DisplayMode.Shaded
        elif display_mode_model == 'surface':
            model.sensor_grids.display_mode = DisplayMode.Surface
        elif display_mode_model == 'surfacewithedges':
            model.sensor_grids.display_mode = DisplayMode.SurfaceWithEdges
        elif display_mode_model == 'wireframe':
            model.sensor_grids.display_mode = DisplayMode.Wireframe
        elif display_mode_model == 'points':
            model.sensor_grids.display_mode = DisplayMode.Points

        # Set a default camera if there are not cameras in the model
        if not model.cameras:
            # Use the centroid of the model for the camera position
            actors = Actor.from_model(model=model)
            camera = Camera(position=Actor.get_centroid(actors), type='l')
            cameras = [camera]
        else:
            cameras = model.cameras

        actors = Actor.from_model(model)

        scene = Scene(background_color=background_color)
        scene.add_actors(actors)
        scene.add_cameras(cameras)

        output = scene.export_images(
            folder=folder, name=name, image_type=image_type,
            image_width=image_width, image_height=image_height)

    except Exception as e:
        raise ClickException(f'Translation failed:\n{e}')
    else:
        print(f'Success: {output}', file=sys.stderr)
        return sys.exit(0)