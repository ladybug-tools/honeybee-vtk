

import pathlib
import sys
import click
import traceback

from honeybee_vtk.model import Model
from honeybee_vtk.vtkjs.schema import SensorGridOptions, DisplayMode
from honeybee_vtk.types import ImageTypes


@click.group()
def export_grid():
    """Honeybee VTK commands entry point."""
    pass


@export_grid.command('export-grid-images')
@click.argument('hbjson-file')
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
    '--image-width', '-iw', type=int, default=0, help='Width of images in pixels.'
    ' If not set, Radiance default x dimension of view will be used.', show_default=True
)
@click.option(
    '--image-height', '-ih', type=int, default=0, help='Height of images in pixels.'
    'If not set, Radiance default y dimension of view will be used.', show_default=True
)
@click.option(
    '--background-color', '-bc', type=(int, int, int), default=(255, 255, 255),
    help='Set background color for images', show_default=True
)
@click.option(
    '--grid-option', '-go',
    type=click.Choice(['points', 'meshes'], case_sensitive=False),
    default='meshes', help='Export sensor grids as either points or meshes.',
    show_default=True,
)
@click.option(
    '--grid-display-mode', '-gdm',
    type=click.Choice(['shaded', 'surfacewithedges', 'points'], case_sensitive=False),
    default='surfacewithedges', help='Set display mode for the Sensorgrids.',
    show_default=True
)
@click.option(
    '--config', '-cf', help='File Path to the config json file which can be used to'
    ' mount simulation data on HBJSON.', type=click.Path(exists=True), default=None,
    show_default=True
)
def export_grid(
        hbjson_file, folder, image_type, image_width, image_height,
        background_color, grid_option, grid_display_mode, config):
    """Export images from radiance views in a HBJSON file.

    \b
    Args:
        hbjson-file: Path to an HBJSON file.

    """
    folder = pathlib.Path(folder)
    folder.mkdir(exist_ok=True)

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

    if grid_option == 'points':
        grid_option = SensorGridOptions.Sensors
    elif grid_option == 'meshes':
        grid_option = SensorGridOptions.Mesh

    if grid_display_mode == 'shaded':
        grid_display_mode = DisplayMode.Shaded
    elif grid_display_mode == 'surfacewithedges':
        grid_display_mode = DisplayMode.SurfaceWithEdges
    elif grid_display_mode == 'points':
        grid_display_mode = DisplayMode.Points

    try:
        model = Model.from_hbjson(hbjson=hbjson_file, load_grids=grid_option)
        output = model.to_grid_images(config, folder=folder,
                                      grid_display_mode=grid_display_mode,
                                      background_color=background_color,
                                      image_type=image_type,
                                      image_width=image_width,
                                      image_height=image_height)

    except Exception:
        traceback.print_exc()
        sys.exit(1)
    else:
        print(f'Success: {output}', file=sys.stderr)
        return sys.exit(0)
