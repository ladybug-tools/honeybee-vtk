"""Functionality for image processing."""


import tempfile
import cv2
import glob
import shutil
import pathlib
from ladybug.dt import DateTime
from typing import List
from PIL import Image, ImageDraw, ImageFont, ImageFilter


def write_transparent_background_image(image_path: pathlib.Path,
                                       target_folder: pathlib.Path):
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


def write_transparent_background_images(folder_path: pathlib.Path,
                                        target_folder: pathlib.Path):
    for image_path in list(folder_path.iterdir()):
        write_transparent_background_image(image_path, target_folder)


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


def write_translucent_image(image_path: pathlib.Path, target_folder: pathlib.Path,
                            transparency: int = 200):
    im_rgb = Image.open(image_path.as_posix())
    im_rgba = im_rgb.copy()
    im_rgba.putalpha(transparency)
    im_rgba.save(f'{target_folder}/{image_path.stem}.png')


def write_translucent_images(folder_path: pathlib.Path, target_folder: pathlib.Path,
                             transparency: int = 200):
    """Create a translucent png from a folder of images."""
    for image_path in list(folder_path.iterdir()):
        write_translucent_image(image_path, target_folder, transparency)


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
    # last_image_path = image_paths[-1]
    # last_blended_image_path = f'{target_folder}/{len(image_paths)-1}_blended.png'
    # write_blended_png(last_blended_image_path, last_image_path,
    #                   target_folder, len(image_paths), 0.4)

    shutil.rmtree(temp_folder.as_posix())


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


def export_gif(images_folder: str, target_folder: str):
    """Create a gif from a folder of images."""

    images_path = pathlib.Path(images_folder)
    assert images_path.is_dir(), 'The images folder must be a directory.'

    if not target_folder:
        target_path = images_path
    else:
        target_path = pathlib.Path(target_folder)
        assert target_path.is_dir(), 'The target folder must be a directory.'

    text_on_images: List[str] = []
    temp_folder = pathlib.Path(tempfile.mkdtemp())
    print(f'Temp folder is {temp_folder}')
    serialized_images_folder = temp_folder.joinpath('serialized')
    serialized_images_folder.mkdir()

    for grid_folder in list(images_path.iterdir()):
        # grid_gif_folder = target_path.joinpath(f'{grid_folder.stem}_images')
        # if grid_gif_folder.is_dir():
        #     shutil.rmtree(grid_gif_folder)
        # grid_gif_folder.mkdir()

        image_names = []

        for time_step_count, time_step_folder in enumerate(list(grid_folder.iterdir())):
            for image_count, image_path in enumerate(list(time_step_folder.iterdir())):
                image_names.append(f'{time_step_count}_{image_count}')

        image_names_dict = {image_name: count for count,
                            image_name in enumerate(list(image_names))}

        for time_step_count, time_step_folder in enumerate(list(grid_folder.iterdir())):
            for image_count, image_path in enumerate(list(time_step_folder.iterdir())):
                write_renamed_image(image_path, serialized_images_folder,
                                    str(image_names_dict[
                                        f'{time_step_count}_{image_count}']))
                text_on_images.append(hoy_to_text(image_path))

    translucent_images_folder = temp_folder.joinpath('translucent')
    transparent_images_folder = temp_folder.joinpath('transparent')
    # blended_images_folder = temp_folder.joinpath('blended')
    composite_images_folder = temp_folder.joinpath('composite')
    # # pasted_images_folder = temp_folder.joinpath('pasted')
    # border_images_folder = temp_folder.joinpath('border')
    annotated_images_folder = temp_folder.joinpath('annotated')

    transparent_images_folder.mkdir()
    # blended_images_folder.mkdir()
    translucent_images_folder.mkdir()
    composite_images_folder.mkdir()
    # # pasted_images_folder.mkdir()
    # border_images_folder.mkdir()
    annotated_images_folder.mkdir()

    write_translucent_images(serialized_images_folder, translucent_images_folder, 25)
    # write_blended_images_cv2(serialized_images_folder, blended_images_folder)
    write_transparent_background_images(
        translucent_images_folder, transparent_images_folder)
    # write_blended_images(transparent_images_folder, blended_images_folder)

    # # write_pasted_images(translucent_images_folder, pasted_images_folder)
    # write_bordered_images(transparent_images_folder, border_images_folder)

    write_composite_images(transparent_images_folder, composite_images_folder)

    write_annotated_images(composite_images_folder,
                           annotated_images_folder, text_on_images)

    # write_mp4_from_images(annotated_images_folder, target_path)
    write_gif(annotated_images_folder, target_path)
    # write_apng(annotated_images_folder, target_path)

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
                write_translucent_image(image_path, translucent_folder)
                translucent_image_path = translucent_folder.joinpath(
                    f'{image_path.stem}.png')
                write_transparent_background_image(
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
