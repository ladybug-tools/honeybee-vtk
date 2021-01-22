"""Write either an HTML or a .zip of VTk or XML files from a valid HBJSON."""

import os
import json
import warnings
import vtk

from .file_writers import write_files, write_html


def writer(file_path, *, file_name=None, target_folder=None, include_grids=False,
           include_vectors=False, include_points=False, writer='html', open_html=False):
    """Read a valid HBJSON and either write an HTML or a .zip of VTK files.

    Args:
        file_path: A text string for a valid path to the HBJSON file.
        file_name: A text string for the name of the .zip file to be written. If no
            text string is provided, the name of the HBJSON file will be used as a
            file name for the .zip file.
        target_folder: A text string to a folder to write the output file. The file
            will be written to the current folder if not provided.
        include_grids: A boolean. Defaults to False. Grids will not be extracted from
            HBJSON if set to False.
        include_vectors: A boolean. Defaults to False. Vector arrows will not be created
            if set to False.
        include_points: A boolean. Defaults to False. If set to True, sensor points
            color-grouped based on their vector direction will be exported instead of
            arrows for the vectors.
        writer: A text string to indicate the VTK writer. Acceptable values are
            'vtk', 'xml', and 'html'. Defaults to 'html'.
        open_html: A boolean. If set to True, it will open the generated HTML
            in a web browser when 'html' is provided as value in the writer argument.
            Defaults to False.

    Returns:
        A text string containing the path to the output file.
    """

    # Check if path to HBJSON is fine
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f'The path is not a valid path:{file_path}')

    # Check if the file is a valid JSON
    try:
        with open(file_path) as fp:
            hbjson = json.load(fp)
    except json.decoder.JSONDecodeError:
        raise ValueError(f'Not a valid JSON file: {file_path}')

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

        if include_vectors:
            include_points = False

        if writer.lower() == 'html':
            return write_html(
                hbjson, file_path, file_name, target_folder, include_grids,
                include_vectors, include_points, open_html)

        elif writer.lower() == 'xml':
            vtk_writer = vtk.vtkXMLPolyDataWriter()
            vtk_extension = '.vtp'
            return write_files(
                hbjson, file_path, file_name, target_folder, include_grids,
                include_vectors, include_points, vtk_writer, vtk_extension)

        elif writer.lower() == 'vtk':
            vtk_writer = vtk.vtkPolyDataWriter()
            vtk_extension = '.vtk'
            return write_files(
                hbjson, file_path, file_name, target_folder, include_grids,
                include_vectors, include_points, vtk_writer, vtk_extension)

        else:
            raise ValueError(writer_error)

    else:
        raise ValueError(writer_error)
