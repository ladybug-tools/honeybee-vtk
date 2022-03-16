"""Functionality for image processing."""


import tempfile
import cv2
import glob
import shutil
import pathlib
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
    image_data = image.getdata()

    new_image_data = []
    for pixel in image_data:
        if pixel[0] == 255 and pixel[1] == 255 and pixel[2] == 255:
            new_image_data.append((255, 255, 255, 0))
        else:
            new_image_data.append(pixel)

    image.putdata(new_image_data)
    return image


def write_composite_png(image_path_1: pathlib.Path, image_path_2: pathlib.Path,
                        temp_folder: pathlib.Path,
                        target_folder: pathlib.Path, number: int):
    """Create a blended png from a folder of images."""
    image_1 = Image.open(image_path_1)
    image_2 = Image.open(image_path_2)
    composite = Image.alpha_composite(image_2, image_1)
    composite.save(f'{temp_folder}/{number}_composite.png', 'PNG')
    composite.save(f'{target_folder}/{image_path_1.stem}.png', 'PNG')


def write_composite_images(folder_path: pathlib.Path, target_folder: pathlib.Path):
    """Create a blended png from a folder of images."""
    temp_folder = target_folder.joinpath('temp')
    temp_folder.mkdir()

    number_file_dict = {
        int(file_path.stem): file_path for file_path in list(folder_path.iterdir())}
    sorted_file_numbers: List[int] = sorted(number_file_dict.keys())

    file_0 = number_file_dict[sorted_file_numbers[0]]
    first_composite = Image.open(file_0)
    first_composite.save(f'{temp_folder}/0_composite.png', 'PNG')
    first_composite.save(f'{target_folder}/{file_0.stem}.png', 'PNG')

    for i in range(1, len(sorted_file_numbers)):
        image_path_1 = number_file_dict[sorted_file_numbers[i]]
        image_path_2 = pathlib.Path(f'{temp_folder}/{i-1}_composite.png')
        write_composite_png(image_path_1, image_path_2, temp_folder, target_folder, i)

    shutil.rmtree(temp_folder.as_posix())


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
    print(image_rgba.info)
    return image_rgba


def write_gif(folder_path: pathlib.Path, target_folder: pathlib.Path,
              name: str = 'output'):

    number_file_dict = {
        int(file_path.stem): file_path for file_path in list(folder_path.iterdir())}
    sorted_file_numbers: List[int] = sorted(number_file_dict.keys())

    images = [Image.open(number_file_dict[number]) for number in sorted_file_numbers]
    image = images[0]
    rest_of_images = images[1:] + [images[-1]]+[images[-1]]+[images[-1]]
    image.save(f'{target_folder}/{name}.gif', save_all=True,
               append_images=rest_of_images, duration=1000, loop=0,
               transparency=0, format='GIF', disposal=2)


def write_apng(folder_path: pathlib.Path, target_folder: pathlib.Path,
               name: str = 'output'):
    number_file_dict = {
        int(file_path.stem): file_path for file_path in list(folder_path.iterdir())}
    sorted_file_numbers: List[int] = sorted(number_file_dict.keys())

    images = [Image.open(number_file_dict[number]) for number in sorted_file_numbers]
    image = images[0]
    rest_of_images = images[1:] + [images[-1]]+[images[-1]]+[images[-1]]
    image.save(f'{target_folder}/{name}.png', save_all=True,
               append_images=rest_of_images, duration=1000, loop=0)


def write_blended_image_cv2(image_paths: List[pathlib.Path],
                            target_folder: pathlib.Path, number: int):

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

    cv2.imwrite(f'{target_folder}/{number}_blended.png', dst)


def write_blended_images_cv2(folder_path: pathlib.Path, target_folder: pathlib.Path):

    temp_folder = target_folder.joinpath('temp')
    temp_folder.mkdir()

    number_file_dict = {
        int(file_path.stem): file_path for file_path in list(folder_path.iterdir())}
    sorted_file_numbers: List[int] = sorted(number_file_dict.keys())

    image_paths = [number_file_dict[number] for number in sorted_file_numbers]
    for i in range(1, len(image_paths)+1):
        write_blended_image_cv2(image_paths[:i], temp_folder, i-1)

    number_file_dict_temp = {
        int(file_path.stem.split('_')[0]): file_path for file_path in list(temp_folder.iterdir())}
    sorted_file_numbers_temp: List[int] = sorted(number_file_dict_temp.keys())

    temp_image_paths = [number_file_dict_temp[number]
                        for number in sorted_file_numbers_temp]
    for count, image_path in enumerate(temp_image_paths):
        write_renamed_image(image_path, target_folder, str(count))

    shutil.rmtree(temp_folder.as_posix())


def hoy_to_text(image_path: pathlib.Path) -> str:
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


def write_annotated_image(image_path: pathlib.Path, target_folder: pathlib.Path,
                          text: str, image_name: str = None):
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


def write_annotated_images(folder_path: pathlib.Path, target_folder: pathlib.Path,
                           text_on_images: List[str]):
    assert len(text_on_images) == len(list(folder_path.iterdir())),\
        f'Number of images in {folder_path} does not match number of image names.'

    number_file_dict = {
        int(file_path.stem): file_path for file_path in list(folder_path.iterdir())}
    sorted_file_numbers: List[int] = sorted(number_file_dict.keys())

    for count, number in enumerate(sorted_file_numbers):
        write_annotated_image(
            number_file_dict[number], target_folder, text_on_images[count])


def write_renamed_image(image_path: pathlib.Path, target_folder: pathlib.Path,
                        image_name: str):
    image = Image.open(image_path)
    image.save(f'{target_folder}/{image_name}.png', 'PNG')


def write_renamed_images(folder_path: pathlib.Path, target_folder: pathlib.Path):
    for count, image_path in enumerate(list(folder_path.iterdir())):
        write_renamed_image(image_path, target_folder, f'{count}')


def write_mp4_from_images(images_folder: pathlib.Path, target_folder: pathlib.Path = None,
                          file_name: str = 'output'):
    """Create an mp4 video from a folder of images."""
    target_folder = target_folder or images_folder

    number_file_dict = {
        int(file_path.stem): file_path for file_path in list(images_folder.iterdir())}
    sorted_file_numbers: List[int] = sorted(number_file_dict.keys())

    img_array = []
    for file_path in [number_file_dict[number] for number in sorted_file_numbers]:
        for file in glob.glob(file_path.as_posix()):
            img = cv2.imread(file)
            height, width, layers = img.shape
            size = (width, height)
            img_array.append(img)

    file_path = f'{target_folder.as_posix()}/{file_name}.mp4'
    out = cv2.VideoWriter(file_path, cv2.VideoWriter_fourcc(*'mp4v'), 1, size)

    for i in range(len(img_array)):
        out.write(img_array[i])
    out.release()


def _serialized_images_and_timestamps(
        grid_folder: pathlib.Path, temp_folder: pathlib.Path) -> Tuple[pathlib.Path,
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


def _files_in_order(temp_folder: pathlib.Path, parent: str,
                    number_of_images: int) -> List[pathlib.Path]:
    """Return a list of file paths in order."""
    return [temp_folder.joinpath(f'{parent}/{i}.png') for i in range(number_of_images)]


def _transparent_translucent(temp_folder: pathlib.Path, images_folder: pathlib.Path,
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


def export_gif(time_step_images_path: str, target_path: str):
    """Write a gif from a folder of images."""

    time_step_images_folder = pathlib.Path(time_step_images_path)
    assert time_step_images_folder.is_dir(), 'The images folder must be a directory.'

    if not target_path:
        target_folder = time_step_images_folder
    else:
        target_folder = pathlib.Path(target_path)
        assert target_folder.is_dir(), 'The target folder must be a directory.'

    for grid_folder in list(time_step_images_folder.iterdir()):

        # create a folder to save the GIF
        grid_gif_folder = target_folder.joinpath(f'{grid_folder.stem}_gif')
        if grid_gif_folder.is_dir():
            shutil.rmtree(grid_gif_folder)
        grid_gif_folder.mkdir()

        temp_folder = pathlib.Path(tempfile.mkdtemp())

        serialized_images_folder, time_stamp_strings = _serialized_images_and_timestamps(
            grid_folder, temp_folder)

        # blended_images_folder = temp_folder.joinpath('blended')
        composite_images_folder = temp_folder.joinpath('composite')
        annotated_images_folder = temp_folder.joinpath('annotated')

        # blended_images_folder.mkdir()
        composite_images_folder.mkdir()
        annotated_images_folder.mkdir()

        # write_blended_images_cv2(serialized_images_folder, blended_images_folder)
        trans_folder = _transparent_translucent(temp_folder, serialized_images_folder)
        # write_blended_images(transparent_images_folder, blended_images_folder)
        write_composite_images(trans_folder,
                               composite_images_folder)

        write_annotated_images(composite_images_folder,
                               annotated_images_folder, time_stamp_strings)
        write_gif(annotated_images_folder, grid_gif_folder)

        # try:
        #     shutil.rmtree(temp_folder)
        # except Exception:
        #     pass


def get_transparent_images(images_folder: str, target_folder: str = None):
    """A folder of images with transparent grid and a fully transparent background."""

    images_path = pathlib.Path(images_folder)
    assert images_path.is_dir(), 'The images folder must be a directory.'

    if not target_folder:
        target_path = images_path
    else:
        target_path = pathlib.Path(target_folder)
        assert target_path.is_dir(), 'The target folder must be a directory.'

    for grid_folder in list(images_path.iterdir()):
        grid_image_folder = target_path.joinpath(f'{grid_folder.stem}_images')
        if grid_image_folder.is_dir():
            shutil.rmtree(grid_image_folder)

        grid_image_folder.mkdir()
        temp_folder = pathlib.Path(tempfile.mkdtemp())
        renamed_folder = temp_folder.joinpath('renamed')
        renamed_folder.mkdir()
        translucent_folder = temp_folder.joinpath('translucent')
        translucent_folder.mkdir()
        transparent_folder = temp_folder.joinpath('transparent')
        transparent_folder.mkdir()

        for time_step_count, time_step_folder in enumerate(list(grid_folder.iterdir())):
            for image_count, image_path in enumerate(list(time_step_folder.iterdir())):
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
