

import pathlib
import sys
import click
import traceback
import tempfile
import shutil

from honeybee_vtk.model import Model
from honeybee_vtk.vtkjs.schema import SensorGridOptions, DisplayMode
from honeybee_vtk.types import ImageTypes
from honeybee_vtk.text_actor import TextActor
from honeybee_vtk.timestep_images import export_timestep_images, _extract_periods_colors
from honeybee_vtk.image_processing import write_gif, write_transparent_images


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
    '--text-content', type=str, default=None, show_default=True, help='Text to be '
    'displayed on an image of a grid. This will put this same text on all of the images.'
)
@click.option(
    '--text-height', '-th', type=int, default=15, show_default=True,
    help='Set the height of the text in pixels for the text that will be added to the'
    ' image of a grid.'
)
@click.option(
    '--text-color', '-tc', type=(int, int, int), default=(0, 0, 0), show_default=True,
    help='Set the text color of the text that will added to the image of a grid.'
)
@click.option(
    '--text-position', '-tp', type=(float, float), default=(0.5, 0.0), show_default=True,
    help='Set the text position of the text to added to the image of a grid. The setting'
    ' is applied at the lower left point of the text. (0,0) will give you the lower'
    ' left corner of the image. (1,1) will give you the upper right corner of the image.'
)
@click.option(
    '--text-bold/--text-normal', is_flag=True, default=False, show_default=True,
    help='Set the text to be bold for the text that will added to the image of a grid.'
)
@click.option(
    '--time-step-file-name', '-tfn', type=str, default='', show_default=True,
    help='Name of the time step file without its extension.'
)
@click.option(
    '--periods-file', '-pf', help='File Path to the Periods json file which can be used'
    ' to define time periods and colors. A period is composed of two Ladybug DateTime'
    ' objects. First is the start DateTime and second is the End DateTime. Think of'
    ' these periods as filters of time steps. Images will be generated for these periods'
    ' only. You can also define colors for corresponding periods.',
    type=click.Path(exists=True), default=None, show_default=True
)
@click.option(
    '--flat/--gradient', default=True, show_default=True, help='Indicate'
    ' whether to use flat transparency or gradient transparency in generating time step'
    ' images. If flat is chosen, all the images wil have the same level of transparency.'
    ' If gradient is chosen, the transparency of an image will be lower than the'
    ' transparency of the image coming above.'
)
@click.option(
    '--transparent-images/--no-images', is_flag=True, default=False, show_default=True,
    help='Indicate whether to generate transparent images of each timestep or not.'
)
@click.option(
    '--gif-name', '-gn', type=str, default='output', show_default=True,
    help='Name of the gif file.'
)
@click.option(
    '--gif-duration', '-gd', type=int, default=1000, show_default=True,
    help='Duration of the gif in milliseconds.'
)
@click.option(
    '--gif-loop-count', '-glc', type=int, default=0, show_default=True,
    help='Number of times the gif should loop. 0 means infinite.'
)
@click.option(
    '-gif-linger-last-frame', '-gl', type=int, default=3, show_default=True,
    help='A number that will make the last frame linger for longer than the duration'
    ' by this multiple.'
)
@ click.option(
    '--image-transparency', '-it', type=float, default=0.5, show_default=True,
    help='Set the transparency of the image. 0.0 is fully transparent and 1.0 is fully'
    ' opaque.'
)
def export(
        hbjson_file, folder, image_type, image_width, image_height,
        background_color, model_display_mode, grid_options, grid_display_mode, view,
        config, validate_data, selection, grid_filter, text_content, text_height,
        text_color, text_position, text_bold, time_step_file_name, periods_file, flat,
        transparent_images, gif_name, gif_duration, gif_loop_count,
        gif_linger_last_frame, image_transparency,):
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
            text_actor = TextActor(text=text_content, height=text_height, color=text_color,
                                   position=text_position, bold=text_bold)\
                if text_content else None

            output = model.to_grid_images(config=config, folder=folder,
                                          grid_filter=grid_filter,
                                          grid_display_mode=grid_display_mode,
                                          background_color=background_color,
                                          image_type=image_type,
                                          image_width=image_width,
                                          image_height=image_height,
                                          text_actor=text_actor)
        else:
            periods, grid_colors = _extract_periods_colors(periods_file)

            if not config:
                raise ValueError('Config file not provided.')
            if not time_step_file_name:
                raise ValueError('Time step file name not provided.')
            if not periods:
                raise ValueError('Periods file not provided.')

            if grid_display_mode == DisplayMode.Points:
                print('Grids as points are not supported for image export of timesteps.')
                grid_display_mode = DisplayMode.Shaded

            temp_folder = pathlib.Path(tempfile.mkdtemp())
            output = export_timestep_images(hbjson_path=hbjson_file, config_path=config,
                                            timestamp_file_name=time_step_file_name,
                                            periods=periods, grid_colors=grid_colors,
                                            grid_display_mode=grid_display_mode,
                                            target_folder=temp_folder,
                                            grid_filter=grid_filter,
                                            text_actor=None,
                                            label_images=False)
            if flat:
                write_gif(output, folder.as_posix(), False, gif_name, gif_duration,
                          gif_loop_count, gif_linger_last_frame)
            else:
                write_gif(output, folder.as_posix(), True, gif_name, gif_duration,
                          gif_loop_count, gif_linger_last_frame)

            if transparent_images:
                write_transparent_images(output, folder.as_posix(), image_transparency)

            shutil.rmtree(temp_folder)
            output = folder

    except Exception:
        traceback.print_exc()
        sys.exit(1)
    else:
        print(f'Success: {output}', file=sys.stderr)
        return sys.exit(0)
