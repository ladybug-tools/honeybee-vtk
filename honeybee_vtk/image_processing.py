"""Functionality for image processing."""

import glob
import numpy as np
from pathlib import Path
from PIL import Image
import tempfile
import cv2


def create_mp4_from_images(images_folder: Path, target_folder: Path = Path('.'),
                           file_name: str = 'output'):

    img_array = []
    for file_path in list(images_folder.iterdir()):
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


target_folder = r"C:\Users\devan\OneDrive\Desktop\target"
folder_path = r"C:\Users\devan\OneDrive\Desktop\target"
images_folder = Path(folder_path)
target_folder = Path(target_folder)
create_mp4_from_images(images_folder, target_folder, 'Avehi')
