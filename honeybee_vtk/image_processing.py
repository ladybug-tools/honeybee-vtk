"""Functionality for image processing."""


import tempfile
import cv2
import shutil
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


def write_composite_png(image_path_1: Path, image_path_2: Path,
                        temp_folder: Path,
                        target_folder: Path, number: int):
    """Create a blended png from a folder of images."""
    image_1 = Image.open(image_path_1)
    image_2 = Image.open(image_path_2)
    composite = Image.alpha_composite(image_2, image_1)
    composite.save(f'{temp_folder}/{number}_composite.png', 'PNG')
    composite.save(f'{target_folder}/{image_path_1.stem}.png', 'PNG')


def _composite_folder(temp_folder: Path, images_folder: Path, number_of_images: int):
    """Create a blended png from a folder of images."""

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
        write_composite_png(image_path_1, image_path_2,
                            temp_composite_folder, composite_images_folder, i)

    shutil.rmtree(temp_composite_folder.as_posix())
    return composite_images_folder


def _translucent(image: Image.Image, transparency: int):
    """Set uniform transparency for an image.

    Args:
        image: An Image object.
        transparency: An integer between 0 and 255. 0 is fully transparent and 255 is 
            fully opaque.

    Returns:
        An Image object with a uniform transparency.
    """
    image_rgba = image.copy()
    image_rgba.putalpha(transparency)
    return image_rgba


def write_gif(temp_folder: Path, images_folder: Path, target_folder: Path,
              number_of_images: int, gif_name: str,
              gif_duration: int, gif_loop_count: int):

    image_paths = _files_in_order(temp_folder, images_folder.stem, number_of_images)
    images = [Image.open(image_path) for image_path in image_paths]
    image = images[0]
    rest_of_images = images[1:] + [images[-1]]+[images[-1]]+[images[-1]]
    image.save(f'{target_folder}/{gif_name}.gif', save_all=True,
               append_images=rest_of_images, duration=gif_duration, loop=gif_loop_count,
               transparency=0, format='GIF', disposal=2)


def write_blended_image_cv2(image_paths: List[Path],
                            target_folder: Path, number: int):
    # Import all image files with the .jpg extension

    image_data = []
    for my_file in image_paths:
        this_image = cv2.imread(my_file.as_posix(), cv2.IMREAD_UNCHANGED)
        image_data.append(this_image)

    # Calculate blended image
    dst = image_data[0]
    for i in range(len(image_data)):
        if i == 0:
            pass
        else:
            alpha = 1.0/(i + 1)
            beta = 1.0 - alpha
            dst = cv2.addWeighted(image_data[i], alpha, dst, beta, 0.0)

    # Save blended image
    cv2.imwrite(f'{target_folder}/{number}.png', dst)


def _blended_folder(temp_folder: Path, images_folder: Path, number_of_images: int):

    blended_images_folder = temp_folder.joinpath('blended')
    blended_images_folder.mkdir()

    image_paths = _files_in_order(temp_folder, images_folder.stem, number_of_images)

    for i in range(1, len(image_paths)+1):
        write_blended_image_cv2(image_paths[:i], blended_images_folder, i-1)

    return blended_images_folder


def hoy_to_text(image_path: Path) -> str:
    """Convert a hoy image to text."""
    hoy = float(image_path.stem.split('_')[0])
    text = DateTime.from_hoy(hoy).to_simple_string()
    updated_text = ''
    for count, item in enumerate(list(text.split('_'))):
        if not count == 2:
            updated_text += item + ' '
        else:
            updated_text += item + ':'
    return updated_text.strip()


def write_annotated_image(image_path: Path, target_folder: Path,
                          text: str, text_height: int, image_name: str = None):
    image = Image.open(image_path)
    width, height = image.size
    image_draw = ImageDraw.Draw(image)
    fnt = ImageFont.truetype('assets/arial.ttf', 25)
    image_draw.rectangle(((width/2-width/15), height-25,
                         (width/2+20), height), fill='white')
    image_draw.text(((width/2-width/15), height-25),
                    text, font=fnt, fill='black')
    if not image_name:
        image.save(f'{target_folder}/{image_path.stem}.png', 'PNG')
    else:
        image.save(f'{target_folder}/{image_name}.png', 'PNG')


def _annotated_folder(temp_folder: Path, images_folder: Path,
                      text_on_images: List[str], text_height: int, number_of_images: int):
    assert len(text_on_images) == len(list(images_folder.iterdir())),\
        f'Number of images in {images_folder} does not match number of image names.'

    annotated_images_folder = temp_folder.joinpath('annotated')
    annotated_images_folder.mkdir()

    image_paths = _files_in_order(temp_folder, images_folder.stem, number_of_images)

    for count, image_path in enumerate(image_paths):
        write_annotated_image(
            image_path, annotated_images_folder, text_on_images[count], text_height)

    return annotated_images_folder


def write_renamed_image(image_path: Path, target_folder: Path,
                        image_name: str):
    image = Image.open(image_path)
    image.save(f'{target_folder}/{image_name}.png', 'PNG')


def _serialized_images_and_timestamps(
        grid_folder: Path, temp_folder: Path) -> Tuple[Path,
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
            write_renamed_image(
                image_path, serialized_images_folder, str(image_count))
            time_stamps.append(hoy_to_text(image_path))
            image_count += 1

    return serialized_images_folder, time_stamps


def _files_in_order(temp_folder: Path, parent: str,
                    number_of_images: int) -> List[Path]:
    """Return a list of file paths in order."""
    return [temp_folder.joinpath(f'{parent}/{i}.png') for i in range(number_of_images)]


def _transparent_translucent(temp_folder: Path, images_folder: Path,
                             translucency: bool = True, translucency_value: int = 127):

    trans_folder = temp_folder.joinpath('trans')
    trans_folder.mkdir()

    if translucency:
        for image_path in images_folder.iterdir():
            image = Image.open(image_path.as_posix())
            image = _translucent(image, translucency_value)
            image = _transparent_background(image)
            image.save(f'{trans_folder}/{image_path.stem}.png', 'PNG')
    else:
        for image_path in images_folder.iterdir():
            image = Image.open(image_path.as_posix())
            image = _transparent_background(image)
            image.save(f'{trans_folder}/{image_path.stem}.png', 'PNG')

    return trans_folder


def export_gif(time_step_images_path: str, target_path: str,
               gradient_transparency: bool = False,
               gif_name: str = 'output',
               gif_duration: int = 1000,
               gif_loop_count: int = 0) -> str:
    """Export a gif from a time step images.

    This function will generate one folder for each grid found in the model.

    Args:
        time_step_images_path: The path to the folder containing the images.
            for time steps.
        target_path: The path to the folder to write the gif to.
        gradient_transparency: Whether to use a gradient transparency.
            or not. If chosen a gradient of transparency will be used. Which will make
            the image in the back more transparent compared to the image in the front.
            Defaults to False which will use a flat transparency. which means the
            all images will have same amount of transparency.
        gif_name: The name of the gif. Defaults to 'output'.
        gif_duration: The duration of the gif in milliseconds. Defaults to 1000.
        gif_loop_count: The number of times to loop the gif. Defaults to 0 which will 
            loop infinitely.

    Returns:
        The path to the folder where gifs are exported.
    """

    time_step_images_folder = Path(time_step_images_path)
    assert time_step_images_folder.is_dir(), 'The images folder must be a directory.'

    if not target_path:
        target_folder = time_step_images_folder
    else:
        target_folder = Path(target_path)
        assert target_folder.is_dir(), 'The target folder must be a directory.'

    for grid_folder in list(time_step_images_folder.iterdir()):

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
            gif_images_folder = _transparent_translucent(
                temp_folder, blended_folder, translucency=False)

        else:
            trans_folder = _transparent_translucent(
                temp_folder, serialized_images_folder)
            gif_images_folder = _composite_folder(temp_folder, trans_folder,
                                                  len(time_stamp_strings))

        annotated_folder = _annotated_folder(temp_folder, gif_images_folder,
                                             time_stamp_strings, 18,
                                             len(time_stamp_strings))

        write_gif(temp_folder, annotated_folder,
                  grid_gif_folder, len(time_stamp_strings), gif_name,
                  gif_duration, gif_loop_count)

        try:
            shutil.rmtree(temp_folder)
        except Exception:
            pass

    return target_folder.as_posix()


def export_transparent_images(time_step_images_path: str, target_path: str = None):
    """A folder of images with transparent grid and a fully transparent background."""

    time_step_images_folder = Path(time_step_images_path)
    assert time_step_images_folder.is_dir(), 'The images folder must be a directory.'

    if not target_path:
        target_folder = time_step_images_folder
    else:
        target_folder = Path(target_path)
        assert target_folder.is_dir(), 'The target folder must be a directory.'

    for grid_folder in list(time_step_images_folder.iterdir()):

        grid_gif_folder = target_folder.joinpath(f'{grid_folder.stem}_gif')
        if grid_gif_folder.is_dir():
            shutil.rmtree(grid_gif_folder)
        grid_gif_folder.mkdir()

        temp_folder = Path(tempfile.mkdtemp())

        renamed_folder = temp_folder.joinpath('renamed')
        renamed_folder.mkdir()
        translucent_folder = temp_folder.joinpath('translucent')
        translucent_folder.mkdir()
        transparent_folder = temp_folder.joinpath('transparent')
        transparent_folder.mkdir()

        image_count = 0
        for time_step_folder in grid_folder.iterdir():
            for image_path in time_step_folder.iterdir():

                _translucent(image_path, translucent_folder)
                translucent_image_path = translucent_folder.joinpath(
                    f'{image_path.stem}.png')
                _transparent_background(
                    translucent_image_path, transparent_folder)
                transparent_image_path = transparent_folder.joinpath(
                    f'{image_path.stem}.png')
                text = hoy_to_text(image_path)
                write_annotated_image(
                    transparent_image_path, grid_image_folder, text,
                    f'{time_step_count}_{image_count}')
        try:
            shutil.rmtree(temp_folder)
        except Exception:
            continue

    return target_folder.as_posix()
