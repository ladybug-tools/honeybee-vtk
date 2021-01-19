"""Write either an HTML or VTK files from a valid HBJSON."""

import os
import json
import warnings
import vtk

from .files_writers import write_files
from .html_writers import write_html


def write(file_path, *, file_name=None, target_folder=None, include_grids=True,
          include_vectors=True, writer='html'):
    """Read a valid HBJSON and either write an HTML or a .zip of VTK files.

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
            'vtk', 'xml', and 'html'. Defaults to 'html'.

    Returns:
        A text string containing the path to the output file.
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

    # Set the target folder to write the files
    target_folder = target_folder or os.getcwd()
    if not os.path.exists(target_folder):
        warnings.warn(
            'The path provided at target_folder does not lead to a folder.'
            ' Hence, a new folder is created at the path provided to write the'
            ' file output.')
        os.makedirs(target_folder, exist_ok=True)

    # Validate and set writer and extension
    writer_error = 'The value for writer can be "html", vtk" or "xml" only.'

    # Write files
    if isinstance(writer, str):

        if writer.lower() == 'html':
            write_html(file_path, file_name, target_folder, include_grids,
                       include_vectors, hbjson)
        
        elif writer.lower() == 'xml':
            vtk_writer = vtk.vtkXMLPolyDataWriter()
            vtk_extension = '.vtp'
            return write_files(file_path, file_name, target_folder, include_grids,
                               include_vectors, vtk_writer, vtk_extension, hbjson)

        elif writer.lower() == 'vtk':
            vtk_writer = vtk.vtkPolyDataWriter()
            vtk_extension = '.vtk'
            return write_files(file_path, file_name, target_folder, include_grids,
                               include_vectors, vtk_writer, vtk_extension, hbjson)

        else:
            raise ValueError(writer_error)

    else:
        raise ValueError(writer_error)
