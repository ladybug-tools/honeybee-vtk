"""Functionality for image processing."""


import tempfile
import cv2
import shutil
import sys
from io import BytesIO

from pathlib import Path
from ladybug.dt import DateTime
from typing import List, Tuple
from PIL import Image, ImageDraw, ImageFont


def _transparent_background(image: Image.Image) -> Image.Image:
    """Make a transparent background for an image.

    Args:
        image: An Image object.

    Returns:
        An Image object with a fully transparent background.
    """
    image = image.convert("RGBA")
    image_data = image.getdata()

    new_image_data = []
    for pixel in image_data:
        if pixel[0] == 255 and pixel[1] == 255 and pixel[2] == 255:
            new_image_data.append((255, 255, 255, 0))
        else:
            new_image_data.append(pixel)

    image.putdata(new_image_data)
    return image


def _composite(image_path_1: Path, image_path_2: Path,
               temp_folder: Path,
               target_folder: Path, name: str):
    """Write a composite png from a two images.

    Args:
        image_path_1: A pathlib.Path object for the first image.
        image_path_2: A pathlib.Path object for the second image.
        temp_folder: A pathlib.Path object for the temporary folder.
        target_folder: A pathlib.Path object for the folder to write the composite
            image to.
        name: A string for the name of the composite image.
    """
    image_1 = Image.open(image_path_1)
    image_2 = Image.open(image_path_2)
    composite = Image.alpha_composite(image_2, image_1)
    composite.save(f'{temp_folder}/{name}_composite.png', 'PNG')
    composite.save(f'{target_folder}/{image_path_1.stem}.png', 'PNG')


def _composite_folder(temp_folder: Path, images_folder: Path,
                      number_of_images: int) -> Path:
    """Write a folder of composite images.

    Args:
        temp_folder: A pathlib.Path object for the temporary folder.
        images_folder: A pathlib.Path object to the folder to read images from.
        number_of_images: An integer for the number of images in the folder.

    Returns:
        A pathlib.Path object for the folder of the composite images.
    """

    composite_images_folder = temp_folder.joinpath('composite')
    composite_images_folder.mkdir()

    temp_composite_folder = composite_images_folder.joinpath('temp')
    temp_composite_folder.mkdir()

    image_paths = _files_in_order(temp_folder, images_folder.stem, number_of_images)

    image_path_0 = image_paths[0]
    first_composite = Image.open(image_path_0)
    first_composite.save(f'{temp_composite_folder}/0_composite.png', 'PNG')
    first_composite.save(f'{composite_images_folder}/{image_path_0.stem}.png', 'PNG')

    for i in range(1, len(image_paths)):
        image_path_1 = image_paths[i]
        image_path_2 = Path(f'{temp_composite_folder}/{i-1}_composite.png')
        _composite(image_path_1, image_path_2,
                   temp_composite_folder, composite_images_folder, str(i))

    shutil.rmtree(temp_composite_folder.as_posix())

    return composite_images_folder


def _translucent(image: Image.Image, transparency: float):
    """Set uniform transparency for an image.

    Args:
        image: An Image object.
        transparency: An integer between 0 and 1. 0 is fully transparent and 1 is
            fully opaque.

    Returns:
        An Image object with a uniform transparency.
    """
    assert 0 <= transparency <= 1, 'Transparency must be a between 0 and 1 inclusive.'

    image_rgba = image.copy()
    image_rgba.putalpha(round(transparency*255))
    return image_rgba


def _gif(temp_folder: Path, images_folder: Path, target_folder: Path,
         number_of_images: int, gif_name: str,
         gif_duration: int, gif_loop_count: int, linger_last_frame: int = 30) -> None:
    """Write a gif from a folder of images.

    Args:
        temp_folder: A pathlib.Path object for the temporary folder.
        images_folder: A pathlib.Path object to the folder to read images from.
        target_folder: A pathlib.Path object for the folder to write the GIF to.
        number_of_images: An integer for the number of images in the folder.
        gif_name: A string for the name of the GIF.
        gif_duration: An integer for the duration of each frame in the GIF in 
            milliseconds.
        gif_loop_count: An integer for the number of times to loop the GIF.
        linger_last_frame: An integer that will make the last frame linger for longer
            than the duration. If set to 0, the last frame will not linger. Setting it
            to 3 will make the last frame linger for 3 times the duration. Defaults to
            3.
    """

    image_paths = _files_in_order(temp_folder, images_folder.stem, number_of_images)
    images = [Image.open(image_path) for image_path in image_paths]
    image = images[0]
    rest_of_images = images[1:] + [images[-1]]*linger_last_frame
    image.save(f'{target_folder}/{gif_name}.gif', save_all=True,
               append_images=rest_of_images, duration=gif_duration, loop=gif_loop_count,
               transparency=0, format='GIF', disposal=2)


def _blended_image(image_paths: List[Path],
                   target_folder: Path, name: str) -> None:
    """Write a blended image.

    Args:
        image_paths: A list of pathlib.Path objects for the images to blend into one.
        target_folder: A pathlib.Path object for the folder to write the blended image 
            to.
        number: A text representing the name of the image to write.
    """
    image_data = []
    for my_file in image_paths:
        this_image = cv2.imread(my_file.as_posix(), cv2.IMREAD_UNCHANGED)
        image_data.append(this_image)

    dst = image_data[0]
    for i in range(len(image_data)):
        if i == 0:
            pass
        else:
            alpha = 1.0/(i + 1)
            beta = 1.0 - alpha
            dst = cv2.addWeighted(image_data[i], alpha, dst, beta, 0.0)

    cv2.imwrite(f'{target_folder}/{name}.png', dst)


def _blended_folder(temp_folder: Path, images_folder: Path,
                    number_of_images: int) -> Path:
    """Write a folder of blended images.

    Args:
        temp_folder: A pathlib.Path object for the temporary folder.
        images_folder: A pathlib.Path object to the folder to read images from.
        number_of_images: An integer for the number of images in the folder.

    Returns:
        A pathlib.Path object for the folder of blended images.
    """

    blended_images_folder = temp_folder.joinpath('blended')
    blended_images_folder.mkdir()

    image_paths = _files_in_order(temp_folder, images_folder.stem, number_of_images)

    for i in range(1, len(image_paths)+1):
        _blended_image(image_paths[:i], blended_images_folder, str(i-1))

    return blended_images_folder


def _hoy_to_text(image_path: Path) -> str:
    """Convert a hoy image to text.

    This function reads the HOY from the image name and converts it to a text.

    Args:
        image_path: A path to a hoy image.

    Returns:
        A text that is the HOY converted into a humand readable form.
    """
    hoy = float(image_path.stem.split('_')[0])
    text = DateTime.from_hoy(hoy).to_simple_string()
    updated_text = ''
    for count, item in enumerate(list(text.split('_'))):
        if not count == 2:
            updated_text += item + ' '
        else:
            updated_text += item + ':'
    return updated_text.strip()


def _annotate_image(image: Image.Image, text: str, text_height: int):
    """Add text to an image object.

    Args:
        image: An Image object.
        text: A string.
        text_height: An integer.

    Returns:
        An Image object with text added.
    """

    width, height = image.size
    image_draw = ImageDraw.Draw(image)

    try:
        fnt = ImageFont.truetype('arial.ttf', text_height)
    except OSError:
        fnt = ImageFont.load_default()

    image_draw.rectangle(((width/2-width/15), height-text_height,
                         (width/2+20), height), fill='white')
    image_draw.text(((width/2-width/15), height-text_height),
                    text, font=fnt, fill='black')
    return image


def _annotated_folder(temp_folder: Path, images_folder: Path,
                      text_on_images: List[str],
                      text_height: int,
                      number_of_images: int) -> Path:
    """Annotate images with text.

    This function reads all the images in the images_folder and annotates them with
    the text in text_on_images.

    Args:
        temp_folder: A path to the temp folder.
        images_folder: A path to the folder from which images are read.
        text_on_images: A list of strings to be added to the images as annotation.
        text_height: The height of the text.
        number_of_images: The number of images in the images_folder.

    Returns:
        A path to the folder with annotated images.
    """
    assert len(text_on_images) == len(list(images_folder.iterdir())),\
        f'Number of images in {images_folder} does not match number of image names.'

    annotated_images_folder = temp_folder.joinpath('annotated')
    annotated_images_folder.mkdir()

    image_paths = _files_in_order(temp_folder, images_folder.stem, number_of_images)

    for count, image_path in enumerate(image_paths):
        image = Image.open(image_path)
        image = _annotate_image(image, text_on_images[count], text_height)
        image.save(f'{annotated_images_folder}/{image_path.stem}.png', 'PNG')

    return annotated_images_folder


def _rename_image(image_path: Path, target_folder: Path,
                  image_name: str) -> None:
    """Rename an image.

    Args:
        image_path: A pathlib.Path object for path to the image.
        target_folder: A pathlib.Path object for the target folder where the renamed
            image will be written.
        image_name: A string to be used as the name of the image.
    """
    image = Image.open(image_path)
    image.save(f'{target_folder}/{image_name}.png', 'PNG')


def _serialized_images_and_timestamps(grid_folder: Path,
                                      temp_folder: Path) -> Tuple[Path,
                                                                  List[str]]:
    """Write serialized images and get a list of timestamp strings.

    We are iterating through all the time period folders and pulling images out of them.
    We are renaming these images based on the image count before writing to a folder
    named 'serialized'. This helps us down the line when we need to use the images in
    order. While translating, we're also generating the time stamp annotation to put
    on the images later.

    Args:
        grid_folder: The folder containing the time period folders.
        temp_folder: The folder to write the serialized images to.

    Returns:
        A tuple of two items:

        -   The path to the folder containing the serialized images.
        -   A list of timestamps as text strings.
    """
    time_stamps: List[str] = []
    serialized_images_folder = temp_folder.joinpath('serialized')
    serialized_images_folder.mkdir()

    image_count = 0
    for time_step_folder in list(grid_folder.iterdir()):
        for image_path in list(time_step_folder.iterdir()):
            _rename_image(
                image_path, serialized_images_folder, str(image_count))
            time_stamps.append(_hoy_to_text(image_path))
            image_count += 1

    return serialized_images_folder, time_stamps


def _files_in_order(temp_folder: Path, parent: str,
                    number_of_images: int) -> List[Path]:
    """Return a list of file paths in order.

    This function helps you read files in order from a folder. When ordering the strings
    11 will come after 1 in stead of 2. This function helps you bypass that and read
    the files in order.

    Args:
        temp_folder: Path to the temp folder.
        parent: The name of the folder to read from.

    Returns:
        A list of file paths in order.
    """
    return [temp_folder.joinpath(f'{parent}/{i}.png') for i in range(number_of_images)]


def _transparent_translucent(temp_folder: Path, images_folder: Path,
                             translucency: bool = True) -> Path:
    """Appply transparency to images and make the background translucent.

    Args:
        temp_folder: Path to the temp folder.
        images_folder: The folder containing the images to appply transparency to.
        translucency: A boolean to determine if the transparency should be applied.
            Defaults to True.

    Returns:
        The path to the folder containing the images with transparency applied and 
        background made transparent.
    """
    trans_folder = temp_folder.joinpath('trans')
    trans_folder.mkdir()

    if translucency:
        for image_path in images_folder.iterdir():
            image = Image.open(image_path.as_posix())
            image = _translucent(image, 0.5)
            image = _transparent_background(image)
            image.save(f'{trans_folder}/{image_path.stem}.png', 'PNG')
    else:
        for image_path in images_folder.iterdir():
            image = Image.open(image_path.as_posix())
            image = _transparent_background(image)
            image.save(f'{trans_folder}/{image_path.stem}.png', 'PNG')

    return trans_folder


def write_gif(time_step_images_path: str, target_path: str = '.',
              gradient_transparency: bool = False,
              gif_name: str = 'output',
              gif_duration: int = 1000,
              gif_loop_count: int = 0,
              linger_last_frame: int = 3) -> str:
    """Export a GIF from a time step images.

    This function will generate one folder for each grid found in the model.

    Args:
        time_step_images_path: The path to the folder containing the images.
            for time steps.
        target_path: The path to the folder to write the GIF to. Defaults to current
            working directory.
        gradient_transparency: Whether to use a gradient transparency.
            or not. If chosen a gradient of transparency will be used. Which will make
            the image in the back more transparent compared to the image in the front.
            Defaults to False which will use a flat transparency. which means the
            all images will have same amount of transparency.
        gif_name: The name of the gif. Defaults to 'output'.
        gif_duration: The duration of the gif in milliseconds. Defaults to 1000.
        gif_loop_count: The number of times to loop the gif. Defaults to 0 which will
            loop infinitely.
        linger_last_frame: An integer that will make the last frame linger for longer
            than the duration. If set to 0, the last frame will not linger. Setting it
            to 3 will make the last frame linger for 3 times the duration. Defaults to
            3.

    Returns:
        The path to the folder where GIFs are exported.
    """

    time_step_images_folder = Path(time_step_images_path)
    assert time_step_images_folder.is_dir(), 'The images folder must be a directory.'
    assert len(list(time_step_images_folder.glob('*'))) > 0, 'The images folder must'
    ' not be empty.'

    target_folder = Path(target_path)
    assert target_folder.is_dir(), 'The target folder must be a directory.'

    for grid_folder in time_step_images_folder.iterdir():

        grid_gif_folder = target_folder.joinpath(f'{grid_folder.stem}_gif')
        if grid_gif_folder.is_dir():
            shutil.rmtree(grid_gif_folder)
        grid_gif_folder.mkdir()

        temp_folder = Path(tempfile.mkdtemp())

        serialized_images_folder, time_stamp_strings = _serialized_images_and_timestamps(
            grid_folder, temp_folder)

        if gradient_transparency:
            blended_folder = _blended_folder(temp_folder,
                                             serialized_images_folder,
                                             len(time_stamp_strings))
            gif_images_folder = _transparent_translucent(temp_folder, blended_folder,
                                                         translucency=False)

        else:
            trans_folder = _transparent_translucent(temp_folder,
                                                    serialized_images_folder)
            gif_images_folder = _composite_folder(temp_folder, trans_folder,
                                                  len(time_stamp_strings))

        annotated_folder = _annotated_folder(temp_folder, gif_images_folder,
                                             time_stamp_strings, 25,
                                             len(time_stamp_strings))

        _gif(temp_folder, annotated_folder,
             grid_gif_folder, len(time_stamp_strings), gif_name,
             gif_duration, gif_loop_count, linger_last_frame)

        try:
            shutil.rmtree(temp_folder)
        except Exception:
            pass

    return target_folder.as_posix()


def write_transparent_images(time_step_images_path: str, target_path: str = '.',
                             transparency: float = 0.5) -> str:
    """Write a transparent image for each of the time step images.

    This function will generate one folder for each grid found in the model.

    Args:
        time_step_images_path: The path to the folder containing the images.
            for time steps.
        target_path: The path to the folder where the transparent images will be
            writtend to. Defaults to current working directory.
        transparency: The transparency value to use. Acceptable values are decimal
            point numbers between 0 and 1 inclusive. 0 is completely transparent and 1
             is completely opaque. Defaults to 0.5.

    Returns:
        The path to the folder where the transparent images are written to.
    """

    time_step_images_folder = Path(time_step_images_path)
    assert time_step_images_folder.is_dir(), 'The images folder must be a directory.'
    assert len(list(time_step_images_folder.glob('*'))) > 0, 'The images folder must'
    ' not be empty.'

    target_folder = Path(target_path)
    assert target_folder.is_dir(), 'The target folder must be a directory.'

    for grid_folder in time_step_images_folder.iterdir():

        grid_images_folder = target_folder.joinpath(f'{grid_folder.stem}_images')
        if grid_images_folder.is_dir():
            shutil.rmtree(grid_images_folder)
        grid_images_folder.mkdir()

        temp_folder = Path(tempfile.mkdtemp())

        image_count = 0
        for time_step_folder in grid_folder.iterdir():
            for image_path in time_step_folder.iterdir():
                image = Image.open(image_path.as_posix())
                image = _translucent(image, transparency)
                image = _transparent_background(image)
                text = _hoy_to_text(image_path)
                image = _annotate_image(image, text, 25)
                image.save(f'{grid_images_folder}/{image_count}.png', 'PNG')
                image_count += 1
        try:
            shutil.rmtree(temp_folder)
        except Exception:
            continue

    return target_folder.as_posix()
