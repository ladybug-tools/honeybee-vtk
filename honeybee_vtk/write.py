"""Write vtk files to the disk."""

import os
import json
import warnings
import vtk

from zipfile import ZipFile
from honeybee.typing import clean_string
from .hbjson import read_hbjson, group_by_face_type
from .hbjson import check_grid
from .writers import _write_grids, _write_vectors
from .writers import write_polydata


def write_vtk(file_path, *, file_name=None, target_folder=None, include_grids=True,
              include_vectors=True, writer='vtk'):
    """Read a valid HBJSON and write a .zip of vtk files.

    Args:
        file_path: A text string for a valid path to the HBJSON file.
        file_name: A text string for the name of the .zip file to be written. If no
            text string is provided, the name of the HBJSON file will be used as a
            file name for the .zip file.
        target_folder: A text string to a folder to write the output file. The file
            will be written to the current folder if not provided.
        include_grids: A boolean. Defaults to True. Grids will not be extracted from
            HBJSON if set to False.
        include_vectors: A boolean. Defaults to True. Vector arrows will not be created
            if set to False.
        writer: A text string to indicate the VTK writer. Acceptable values are
            'vtk' and 'xml'. Defaults to 'vtk'.

    Returns:
        A text string containing the path to the .zip that file, which captures all the
            files generated.
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

    # Validate and set writer and extension
    writer_error = 'The value for writer can be either "vtk" or "xml" only.'
    if isinstance(writer, str):
        if writer.lower() == 'vtk':
            vtk_writer = vtk.vtkPolyDataWriter()
            vtk_extension = '.vtk'
        elif writer.lower() == 'xml':
            vtk_writer = vtk.vtkXMLPolyDataWriter()
            vtk_extension = '.vtp'
        else:
            raise ValueError(writer_error)
    else:
        raise ValueError(writer_error)

    # Set the target folder to write the files
    target_folder = target_folder or os.getcwd()
    if not os.path.exists(target_folder):
        warnings.warn(
            'The path provided at target_folder does not lead to a folder.'
            ' Hence, a new folder is created at the path provided to write the'
            ' file output.')
        os.makedirs(target_folder, exist_ok=True)

    # Get points and face_types from HBJSON
    points, hb_types = read_hbjson(hbjson)

    # Get points grouped for each Honeybee face_type
    grouped_points = group_by_face_type(points, hb_types)

    # Write VTK files based on Honeybee face_type and Honeybee object type
    for hb_type in grouped_points:
        write_polydata(grouped_points[hb_type], hb_type, vtk_writer, vtk_extension,
                       target_folder)

    # Names of VTK files to be written
    file_names = list(grouped_points.keys())

    # write grid points to a vtk file if grids are found in HBJSON
    grids = check_grid(hbjson)

    # If grids are there in HBJSON and they are requested
    if grids and include_grids:
        grid_file_names = _write_grids(grids, vtk_writer, vtk_extension, target_folder)
        file_names.extend(grid_file_names)

    # Write vectors if they are requested
    if include_vectors:
        to_write_vectors = [hb_types, grouped_points, grids, include_grids, vtk_writer,
                            vtk_extension, target_folder]
        vector_file_names = _write_vectors(*to_write_vectors)
        file_names.extend(vector_file_names)

    # Use the name of HBJSON if file name is not provided
    if not file_name:
        name = '.'.join(os.path.basename(file_path).split('.')[:-1])
        file_name = clean_string(name)

    # remove extension if provided by user
    file_name = file_name if not file_name.lower().endswith('.zip') else file_name[:-4]
    
    # Create a .zip file to capture all the generated .vtk files
    zip_file = os.path.join(target_folder, file_name + '.zip')
    zipobj = ZipFile(zip_file, 'w')

    # Capture vtk files in a zip file.
    for file_name in file_names:
        file_name = os.path.join(target_folder, file_name + vtk_extension)
        zipobj.write(file_name)
    zipobj.close()

    # Delete vtk files if there is permission
    for file_name in file_names:
        try:
            file_name = os.path.join(target_folder, file_name + vtk_extension)
            os.remove(file_name)
        except OSError:
            warnings.warn(
                f'Honeybee does not have permission to delete {file_names}.'
                ' You may please delete the .vtk files manually.'
            )
    # Return the path where the .zip file is written
    return zip_file
