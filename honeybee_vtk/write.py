"""Write vtk files to the disk."""

import os
import json
import warnings

from zipfile import ZipFile
from honeybee.typing import clean_string
from .hbjson import read_hbjson, group_by_face_type
from .hbjson import check_grid
from .writers import _write_grids, _write_vectors
from .writers import write_polydata


def write_vtk(
        file_path, *, file_name=None, include_grids=True,
        include_vectors=True):

    """Read a valid HBJSON and write a .zip of vtk files.

    Args:
        file_path: A text string for a valid path to the HBJSON file.
        file_name: A text string for the name of the .zip file to be written. If no
            text string is provided, the name of the HBJSON file will be used as a
            file name for the .zip file.
        include_grids: A boolean. Defaults to True. Grids will not be extracted from HBJSON
            if set to False.
        include_vectors: A boolean. Defaults to True. Vector arrows will not be created if
            set to False.
    """

    # Check if path to HBJSON is fine
    if not os.path.isfile(file_path):
        raise FileNotFoundError(
            'The path is not a valid path.'
            ' If file exists, try using double backslashes in file path'
            ' and try again.'
        )

    # Check if the file is a valid JSON
    try:
        with open(file_path) as fp:
            hbjson = json.load(fp)
    except json.decoder.JSONDecodeError:
        raise ValueError(
            'Not a valid JSON file.'
            )

    # Get points and face_types from HBJSON
    points, hb_types = read_hbjson(hbjson)

    # Get points grouped for each Honeybee face_type
    grouped_points = group_by_face_type(points, hb_types)

    # Write VTK files based on Honeybee face_type and Honeybee object type
    for hb_type in grouped_points:
        write_polydata(grouped_points[hb_type], hb_type)

    # Names of VTK files to be written
    file_names = list(grouped_points.keys())

    # write grid points to a vtk file if grids are found in HBJSON
    grids = check_grid(hbjson)

    # If grids are there in HBJSON and they are requested
    if grids and include_grids:
        grid_file_names = _write_grids(grids)
        file_names.extend(grid_file_names)

    # Write vectors if they are requested
    if include_vectors:
        to_write_vectors = [hb_types, grouped_points, grids, include_grids]
        vector_file_names = _write_vectors(*to_write_vectors)
        file_names.extend(vector_file_names)

    # Use the name of HBJSON if file name is not provided
    if not file_name:
        name = '.'.join(os.path.basename(file_path).split('.')[:-1])
        file_name = clean_string(name)
    zip_name = file_name

    # Create a .zip file to capture all the generated .vtk files
    zipobj = ZipFile(file_name + '.zip', 'w')
    
    # Capture vtk files in a zip file.
    for file_name in file_names:
        zipobj.write(file_name + '.vtk')
    zipobj.close()

    # Delete vtk files if there is permission
    for file_name in file_names:
        try:
            os.remove(file_name + '.vtk')
        except OSError:
            warnings.warn(
                f'Honeybee does not have permission to delete {file_names}.'
                ' You may please delete the .vtk files manually.'
            )
    # Return the path where the .zip file is written
    return os.path.join(os.getcwd(), zip_name + '.zip')
    
    