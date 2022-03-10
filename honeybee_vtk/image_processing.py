"""Functionality for image processing."""

import pathlib
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from typing import List
import tempfile
import cv2
import glob
import shutil


def write_transparent_background_images(folder_path: pathlib.Path,
                                        target_folder: pathlib.Path):
    for image_path in list(folder_path.iterdir()):
        image = Image.open(image_path.as_posix())
        image = image.convert("RGBA")
        image_data = image.getdata()

        new_image_data = []
        for pixel in image_data:
            if pixel[0] == 255 and pixel[1] == 255 and pixel[2] == 255:
                new_image_data.append((255, 255, 255, 0))
            else:
                new_image_data.append(pixel)

        image.putdata(new_image_data)
        image.save(f'{target_folder}/{image_path.stem}.png', 'PNG')


def write_blended_png(image_path_1, image_path_2, target_folder: pathlib.Path,
                      number: int, alpha: float = 0.5):
    """Create a blended png from a folder of images."""
    image_1 = Image.open(image_path_1)
    image_2 = Image.open(image_path_2)
    blended = Image.blend(image_1, image_2, alpha=alpha)
    blended.save(f'{target_folder}/{number}_blended.png', 'PNG')


def write_blended_images(folder_path: pathlib.Path, target_folder: pathlib.Path):
    """Create a blended png from a folder of images."""
    files = list(folder_path.iterdir())
    first_blended = Image.open(files[0])
    first_blended.save(f'{target_folder}/0_blended.png', 'PNG')

    for i in range(1, len(files)):
        image_path_1 = files[i]
        image_path_2 = f'{target_folder}/{i-1}_blended.png'
        write_blended_png(image_path_1, image_path_2, target_folder, i)


def write_composite_png(image_path_1, image_path_2, target_folder: pathlib.Path,
                        number: int):
    """Create a blended png from a folder of images."""
    image_1 = Image.open(image_path_1)
    image_2 = Image.open(image_path_2)
    composite = Image.alpha_composite(image_2, image_1)
    composite.save(f'{target_folder}/{number}_composite.png', 'PNG')


def write_composite_images(folder_path: pathlib.Path, target_folder: pathlib.Path):
    """Create a blended png from a folder of images."""
    files = list(folder_path.iterdir())
    first_composite = Image.open(files[0])
    first_composite.save(f'{target_folder}/0_composite.png', 'PNG')

    for i in range(1, len(files)):
        image_path_1 = files[i]
        image_path_2 = f'{target_folder}/{i-1}_composite.png'
        write_composite_png(image_path_1, image_path_2, target_folder, i)


def write_translucent_images(folder_path: pathlib.Path, target_folder: pathlib.Path,
                             transparency: int = 200):
    """Create a translucent png from a folder of images."""
    for image_path in list(folder_path.iterdir()):
        im_rgb = Image.open(image_path.as_posix())
        im_rgba = im_rgb.copy()
        im_rgba.putalpha(transparency)
        im_rgba.save(f'{target_folder}/{image_path.stem}.png')


def write_gif(folder_path: pathlib.Path, target_folder: pathlib.Path,
              name: str = 'Output'):
    images = [(Image.open(f)) for f in list(folder_path.iterdir())]
    image = images[0]
    image.save(f'{target_folder}/{name}.gif', save_all=True,
               append_images=images[1:], duration=500, loop=0, transparency=0,
               format='GIF', disposal=2)


def write_blended_image_cv2(image_paths: List[pathlib.Path],
                            target_folder: pathlib.Path, number: int):
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
    cv2.imwrite(f'{target_folder}/{number}_blended.png', dst)


def write_blended_images_cv2(folder_path: pathlib.Path, target_folder: pathlib.Path):
    image_paths = list(folder_path.iterdir())
    for i in range(1, len(image_paths)+1):
        write_blended_image_cv2(image_paths[:i], target_folder, i-1)
    last_image_path = image_paths[-1]
    last_blended_image_path = f'{target_folder}/{len(image_paths)-1}_blended.png'
    write_blended_png(last_blended_image_path, last_image_path,
                      target_folder, len(image_paths), 0.4)


def write_pasted_png(background_path, foreground_path, target_folder: pathlib.Path,
                     number: int, alpha: float = 0.5):
    """Create a pasted png from a folder of images."""
    background = Image.open(background_path)
    foreground = Image.open(foreground_path)
    background.paste(foreground, (0, 0), foreground)
    background.save(f'{target_folder}/{number}_pasted.png', 'PNG')


def write_pasted_images(folder_path: pathlib.Path, target_folder: pathlib.Path):
    """Create a pasted png from a folder of images."""
    files = list(folder_path.iterdir())
    first_pasted = Image.open(files[0])
    first_pasted.save(f'{target_folder}/0_pasted.png', 'PNG')

    for i in range(1, len(files)):
        background_path = f'{target_folder}/{i-1}_pasted.png'
        foreground_path = files[i]
        write_pasted_png(background_path, foreground_path, target_folder, i)


def apply_border(image_path: str, size: int, color: str = 'black'):

    img = Image.open(image_path)
    width, height = img.size
    edge = img.filter(ImageFilter.FIND_EDGES).load()
    stroke = Image.new(img.mode, img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(stroke)
    for x in range(width):
        for y in range(height):
            if edge[x, y][3] > 0:
                draw.ellipse((x-size, y-size, x+size, y+size), fill=color)
    stroke.paste(img, (0, 0), img)
    return stroke


def write_bordered_images(folder_path: pathlib.Path, target_folder: pathlib.Path):
    """Create a pasted png from a folder of images."""
    for image_path in list(folder_path.iterdir()):
        image = apply_border(image_path.as_posix(), 2)
        image.save(f'{target_folder}/{image_path.stem}.png', 'PNG')


def get_gif(images_folder: str, target_folder: str):
    """Create a gif from a folder of images."""

    images_path = pathlib.Path(images_folder)
    assert images_path.is_dir(), 'The images folder must be a directory.'

    if not target_folder:
        target_path = images_path
    else:
        target_path = pathlib.Path(target_folder)
        assert target_path.is_dir(), 'The target folder must be a directory.'

    temp_folder = pathlib.Path(tempfile.mkdtemp())
    transparent_images_folder = temp_folder.joinpath('transparent')
    blended_images_folder = temp_folder.joinpath('blended')
    translucent_images_folder = temp_folder.joinpath('translucent')
    # composite_images_folder = temp_folder.joinpath('composite')
    # pasted_images_folder = temp_folder.joinpath('pasted')
    # border_images_folder = temp_folder.joinpath('border')

    transparent_images_folder.mkdir()
    blended_images_folder.mkdir()
    translucent_images_folder.mkdir()
    # composite_images_folder.mkdir()
    # pasted_images_folder.mkdir()
    # border_images_folder.mkdir()

    print(temp_folder)
    write_translucent_images(images_path, translucent_images_folder)
    write_transparent_background_images(
        translucent_images_folder, transparent_images_folder)
    # write_blended_images(transparent_images_folder, blended_images_folder)

    # write_pasted_images(translucent_images_folder, pasted_images_folder)

    # write_bordered_images(transparent_images_folder, border_images_folder)
    write_blended_images_cv2(transparent_images_folder, blended_images_folder)
    # write_composite_images(border_images_folder, composite_images_folder)
    write_gif(blended_images_folder, target_path)
