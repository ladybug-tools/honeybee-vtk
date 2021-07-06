

import pathlib
import sys
import click
import traceback

from click.exceptions import ClickException
from pydantic import schema
from honeybee_vtk.actor import Actor
from honeybee_vtk.scene import Scene
from honeybee_vtk.camera import Camera
from honeybee_vtk.model import Model
from honeybee_vtk.vtkjs.schema import SensorGridOptions, DisplayMode
from honeybee_vtk.types import ImageTypes
from honeybee_vtk.config import load_config


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
    '--image-width', '-iw', type=int, default=2500, help='Width of images in pixels.',
    show_default=True
)
@click.option(
    '--image-height', '-ih', type=int, default=2000, help='Height of images in pixels.',
    show_default=True
)
@click.option(
    '--background-color', '-bc', type=(int, int, int), default=(255, 255, 255),
    help='Set background color for images', show_default=True
)
@click.option(
    '--model-display-mode', '-mdm',
    type=click.Choice(['shaded', 'surface', 'surfacewithedges', 'wireframe', 'points'],
                      case_sensitive=False),
    default='shaded', help='Set display mode for the model.', show_default=True
)
@click.option(
    '--grid-options', '-go',
    type=click.Choice(['ignore', 'points', 'meshes'], case_sensitive=False),
    default='ignore', help='Export sensor grids as either points or meshes.',
    show_default=True,
)
@click.option(
    '--grid-display-mode', '-gdm',
    type=click.Choice(['shaded', 'surface', 'surfacewithedges',
                       'wireframe', 'points'], case_sensitive=False),
    default='shaded', help='Set display mode for the Sensorgrids.', show_default=True
)
@click.option(
    '--view', '-vf', help='File Path to the Radiance view file. Multiple view files are'
    ' accepted.', type=click.Path(exists=True), default=None,
    show_default=True, multiple=True
)
@click.option(
    '--config', '-cf', help='File Path to the config json file which can be used to'
    ' mount simulation data on HBJSON.', type=click.Path(exists=True), default=None,
    show_default=True
)
def export(
        hbjson_file, name, folder, image_type, image_width, image_height,
        background_color, model_display_mode, grid_options, grid_display_mode, view,
        config):
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
        if model_display_mode == 'shaded':
            model.update_display_mode(DisplayMode.Shaded)
        elif model_display_mode == 'surface':
            model.update_display_mode(DisplayMode.Surface)
        elif model_display_mode == 'surfacewithedges':
            model.update_display_mode(DisplayMode.SurfaceWithEdges)
        elif model_display_mode == 'wireframe':
            model.update_display_mode(DisplayMode.Wireframe)
        elif model_display_mode == 'points':
            model.update_display_mode(DisplayMode.Points)

        # Set model's grid's display mode
        if grid_display_mode == 'shaded':
            model.sensor_grids.display_mode = DisplayMode.Shaded
        elif model_display_mode == 'surface':
            model.sensor_grids.display_mode = DisplayMode.Surface
        elif model_display_mode == 'surfacewithedges':
            model.sensor_grids.display_mode = DisplayMode.SurfaceWithEdges
        elif model_display_mode == 'wireframe':
            model.sensor_grids.display_mode = DisplayMode.Wireframe
        elif model_display_mode == 'points':
            model.sensor_grids.display_mode = DisplayMode.Points

        actors = Actor.from_model(model)

        scene = Scene(background_color=background_color)
        scene.add_actors(actors)

        # Set a default camera if there are not cameras in the model
        if not model.cameras and not view:
            actors = Actor.from_model(model=model)
            camera = Camera(type='l')
            scene.add_cameras(camera)
            bounds = Actor.get_bounds(actors)
            centroid = Actor.get_centroid(actors)
            aerial_cameras = camera.aerial_cameras(bounds, centroid)
            scene.add_cameras(aerial_cameras)

        else:
            # Collection cameras from model, if the model has it
            if len(model.cameras) != 0:
                cameras = model.cameras
                scene.add_cameras(cameras)

            # if view files are provided collect them
            if view:
                for vf in view:
                    camera = Camera.from_view_file(file_path=vf)
                    scene.add_cameras(camera)

        # load config if provided
        if config:
            load_config(config, model, scene)

        output = scene.export_images(
            folder=folder, name=name, image_type=image_type,
            image_width=image_width, image_height=image_height)

    except Exception:
        traceback.print_exc()
        sys.exit(1)
    else:
        print(f'Success: {output}', file=sys.stderr)
        return sys.exit(0)
