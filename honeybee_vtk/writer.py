"""Write either an HTML or a .zip of VTK or XML files from a valid HBJSON."""

import os
import json
import warnings
import vtk

from .file_writers import write_files, write_html


def writer(file_path, *, file_name=None, target_folder=None, writer='html',
           open_html=False, include_grids=False, include_sensors=None,
           include_normals=None):
    """Read a valid HBJSON and either write an HTML or a .zip of VTK files.

    Args:
        file_path: A text string for a valid path to the HBJSON file.
        file_name: A text string for the name of the .zip file to be written. If no
            text string is provided, the name of the HBJSON file will be used as a
            file name for the .zip file.
        target_folder: A text string to a folder to write the output file. The file
            will be written to the current folder if not provided.
        writer: A text string to indicate the VTK writer. Acceptable values are
            'vtk', 'xml', and 'html'. Defaults to 'html'.
        open_html: A boolean. If set to True, it will open the generated HTML
            in a web browser when 'html' is provided as value in the writer argument.
            Defaults to False.
        include_grids: A boolean. Grids will be exported if the value is True. Here, a
            grid is exported as base-geometry, grid mesh, or sensorpoints in that order
            of preference. So if a Sensorgrid object in HBJSON has base-geometry, then
            that object will be exported as base geometry, eventhough it also might have
            mesh and sensors.
        include_sensors: A text string to indicate whether to show sensor directions as
            vectors or points colored based on directions. Acceptable values are;
            'vectors' and 'points.' Defaults to None.
        include_normals: A text string to indicate whether to show face normals as
            vectors or points colored based on directions. Acceptable values are;
            'vectors' and 'points.' Defaults to None. Currently, this function
            only exports normals for the apertures. Other face types will be supported
            in future.

    Returns:
        A text string containing the path to the output file.
    """

    # Validate include_sensors
    if include_sensors and include_sensors.lower() not in ['vectors', 'points']:
        raise ValueError('The value for include_sensors can be either "vectors"'
                         ' or "points".')

    # Validate include_normals
    if include_normals and include_normals.lower() not in ['vectors', 'points']:
        raise ValueError('The value for include_normals can be either "vectors"'
                         ' or "points".')

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
    if writer.lower() not in ['vtk', 'xml', 'html']:
        raise ValueError('The value for writer can be "html", "vtk" or "xml" only.')
    else:
        writer_val = writer

    if writer_val.lower() == 'html':
        return write_html(
            hbjson, file_path, file_name, target_folder, open_html, include_grids,
            include_sensors, include_normals)

    elif writer_val.lower() == 'xml':
        vtk_writer = vtk.vtkXMLPolyDataWriter()
        vtk_extension = '.vtp'
        return write_files(
            hbjson, file_path, file_name, target_folder, include_grids,
            include_sensors, include_normals, vtk_writer, vtk_extension)

    elif writer_val.lower() == 'vtk':
        vtk_writer = vtk.vtkPolyDataWriter()
        vtk_extension = '.vtk'
        return write_files(
            hbjson, file_path, file_name, target_folder, include_grids,
            include_sensors, include_normals, vtk_writer, vtk_extension)

