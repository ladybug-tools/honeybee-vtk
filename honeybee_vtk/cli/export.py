

import pathlib
import sys
import click
import traceback

from honeybee_vtk.model import Model
from honeybee_vtk.vtkjs.schema import SensorGridOptions, DisplayMode
from honeybee_vtk.types import ImageTypes
from honeybee_vtk.text_actor import TextActor
from honeybee_vtk.timestep_images import export_timestep_images
from ladybug.dt import DateTime


@click.group()
def export():
    """Honeybee VTK commands entry point."""
    pass


@export.command('export-images')
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
    default='shaded', help='Set display mode for the Sensorgrids.',
    show_default=True
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
@click.option(
    '--validate-data', '-vd', is_flag=True, default=False,
    help='Validate simulation data before loading on the model. This is recommended'
    ' when using this command locally.', show_default=True
)
@click.option(
    '--selection', '-sel',
    type=click.Choice(['model', 'grid', 'timesteps'], case_sensitive=False),
    default='model', help='Select what to export.',
    show_default=True
)
@click.option(
    '--grid-filter', '-gf', type=str, default=[], show_default=True, multiple=True,
    help='Filter sensor grids by name. Use this option multiple times to use multiple'
    ' grid identifiers as filters.'
)
@click.option(
    '--text', type=str, default=None, show_default=True, help='Text to be displayed on'
    ' the image.'
)
@click.option(
    '--text-height', '-th', type=int, default=15, show_default=True,
    help='Set the height of the text in pixels.'
)
@click.option(
    '--text-color', '-tc', type=(int, int, int), default=(0, 0, 0), show_default=True,
    help='Set the text color.',
)
@click.option(
    '--text-position', '-tp', type=(float, float), default=(0.5, 0.0), show_default=True,
    help='Set the text position in the image. The setting is applied at the lower left'
    ' point of the text. (0,0) will give you the lower left corner of the image.'
    ' (1,1) will give you the upper right corner of the image.'
)
@click.option(
    '--text-bold', '-tb', is_flag=True, default=False, show_default=True,
    help='Set the text to be bold.'
)
@click.option(
    '--time-step-file-name', '-tfn', type=str, default='', show_default=True,
    help='Name of the time step file.'
)
@click.option(
    '--start-datetime', '-sdt', type=(int, int, int), default=(12, 21, 9),
    show_default=True, help='Set the start datetime to filter the time step file.'
)
@click.option(
    '--end-datetime', '-edt', type=(int, int, int), default=(12, 21, 17),
    show_default=True, help='Set the end datetime to filter the time step file.'
)
def export(
        hbjson_file, folder, image_type, image_width, image_height,
        background_color, model_display_mode, grid_options, grid_display_mode, view,
        config, validate_data, selection, grid_filter, text, text_height, text_color,
        text_position, text_bold, time_step_file_name, start_datetime, end_datetime):
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

    # Set model's display mode
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

    # Set model's grid's display mode
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

        if selection.lower() == 'model':
            output = model.to_images(folder=folder, config=config,
                                     validation=validate_data,
                                     model_display_mode=model_display_mode,
                                     grid_display_mode=grid_display_mode,
                                     background_color=background_color, view=view,
                                     image_type=image_type, image_width=image_width,
                                     image_height=image_height,)

        elif selection.lower() == 'grid':
            text_actor = TextActor(text=text, height=text_height, color=text_color,
                                   position=text_position, bold=text_bold)\
                if text else None

            output = model.to_grid_images(config=config, folder=folder,
                                          grid_filter=grid_filter,
                                          grid_display_mode=grid_display_mode,
                                          background_color=background_color,
                                          image_type=image_type,
                                          image_width=image_width,
                                          image_height=image_height,
                                          text_actor=text_actor)
        else:
            text_actor = TextActor(text=text, height=text_height, color=text_color,
                                   position=text_position, bold=text_bold)\
                if text else None

            if grid_display_mode == DisplayMode.Points:
                print('Grids as points are not supported for image export of timesteps.')
                grid_display_mode = DisplayMode.Shaded

            output = export_timestep_images(hbjson_path=hbjson_file, config_path=config,
                                            timestamp_file_name=time_step_file_name,
                                            st_datetime=DateTime(*start_datetime),
                                            end_datetime=DateTime(*end_datetime),
                                            grid_display_mode=grid_display_mode,
                                            target_folder=folder,
                                            grid_filter=grid_filter)

    except Exception:
        traceback.print_exc()
        sys.exit(1)
    else:
        print(f'Success: {output}', file=sys.stderr)
        return sys.exit(0)
