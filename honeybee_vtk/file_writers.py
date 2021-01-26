"""Functions to write vtk, vtp or HTML files using vtk."""

import os
import vtk
import shutil
import tempfile
import webbrowser
import pathlib
import warnings

from zipfile import ZipFile
from honeybee.typing import clean_string
from .hbjson import check_grid, read_hbjson, group_by_face_type
from .writers import _write_grids, _write_sensors, _write_normals, write_polydata
from .index import write_index_json
from .vtkjs_helper import convert_directory_to_zip_file, add_data_to_viewer


def _write(hbjson, temp_folder, vtk_writer, vtk_extension, include_grids,
           include_sensors, include_normals):
    """Write files to temp folder get the names of files/folders being written.

    Args:
        hbjson: A dictionary.
        temp_folder: Path to the temp folder as a text string.
        vtk_writer: A vtk object. Acceptable values are following;
            vtk.vtkXMLPolyDataWriter(), vtk.vtkPolyDataWriter(), and
            vtk.vtkJSONDataSetWriter() to write XML, VTK, and HTML files respectively.
        vtk_extension: A text string for the file extension to be used. Following are
            acceptable values for the corresponding vtk_writer values;
            '.vtk', '.vtp', ''.
            Please note that the vtk_extension value is a an empty string with no spaces
            in the case of vtk_writer having the value of 'html'.
        include_grids: A bool.
        include_sensors: Bool value of False or a value from 'vectors' or 'points.'
        include_normals: Bool value of False or a value from 'vectors' or 'points.'

    Returns:
        A list of text strings for file names.
    """

    # Get points and face_types from HBJSON
    points, hb_types = read_hbjson(hbjson)

    # Get points grouped for each Honeybee face_type
    grouped_points = group_by_face_type(points, hb_types)

    # Write VTK files based on Honeybee face_type and Honeybee object type
    for hb_type in grouped_points:
        write_polydata(grouped_points[hb_type], hb_type, vtk_writer, vtk_extension,
                       temp_folder)

    # Names of VTK files to be written
    file_names = list(grouped_points.keys())

    # write grid points to a vtk file if grids are found in HBJSON
    if include_grids or include_sensors:
 
        # If grids are there in HBJSON
        grids = check_grid(hbjson)
        if grids:

            # If grids are requested
            if include_grids:
                grid_file_names = _write_grids(
                    grids, vtk_writer, vtk_extension, temp_folder, include_sensors)
                file_names.extend(grid_file_names)

            # If sensors are requested
            if include_sensors:
                sensor_file_names = _write_sensors(
                    include_sensors, grids, vtk_writer, vtk_extension, temp_folder)
                file_names.extend(sensor_file_names)
        else:
            warnings.warn(
                'Grids are not found in HBJSON. include_grids and include_sensors will'
                ' be ignored.')

    # Write normals if they are requested
    if include_normals:
        if 'Aperture' in hb_types:
            normal_file_names = _write_normals(
                include_normals, hb_types, grouped_points, vtk_writer, vtk_extension,
                temp_folder)
            file_names.extend(normal_file_names)
        else:
            warnings.warn(
                'Apertures are not found in HBJSON. include_normals will be ignored.')

    return file_names


def write_files(hbjson, file_path, file_name, target_folder, include_grids,
                include_sensors, include_normals, vtk_writer, vtk_extension):
    """
    Write a .zip of VTK/VTP files.

    Args:
        hbjson: A dictionary.
        file_path: A text string for a valid path to the HBJSON file.
        file_name: A text string for the name of the .zip file to be written. If no
            text string is provided, the name of the HBJSON file will be used as a
            file name for the .zip file.
        target_folder: A text string to a folder to write the output file. The file
            will be written to the current folder if not provided.
        include_grids: A boolean. Defaults to True. Grids will not be extracted from
            HBJSON if set to False.
        include_sensors: A text string to indicate whether to show sensor directions as
            vectors or points colored based on directions. Acceptable values are;
            'vectors' and 'points.' Defaults to False.
        include_normals: A text string to indicate whether to show face normals as
            vectors or points colored based on directions. Acceptable values are;
            'vectors' and 'points.' Defaults to False. Currently, this function
            only exports normals for the apertures. Other face types will be supported
            in future.
        vtk_writer: A vtk object. Acceptable values are following;
            vtk.vtkXMLPolyDataWriter() and vtk.vtkPolyDataWriter() to write XML and
            VTK files respectively.
        vtk_extension: A text string for the file extension to be used. Following are
            acceptable values for the corresponding vtk_writer values;
            vtk.vtkXMLPolyDataWriter() -> '.vtp',
            vtk.vtkPolyDataWriter() -> '.vtk',

    Returns:
        A text string containing the path to the .zip file with VTK/VTP files.
    """
    # Create a temp folder
    temp_folder = tempfile.mkdtemp()

    file_names = _write(
        hbjson, temp_folder, vtk_writer, vtk_extension, include_grids, include_sensors,
        include_normals)

    # Use the name of HBJSON if file name is not provided
    if not file_name:
        name = '.'.join(os.path.basename(file_path).split('.')[:-1])
        file_name = clean_string(name)

    # remove extension if provided by user
    file_name = file_name if not file_name.lower().endswith('.zip') else file_name[:-4]

    # get the absolute path to target folder so it doesn't break for relative paths
    target_folder = os.path.abspath(target_folder)
    # Set a file path for the .zip file in the temp folder
    temp_zip_file = os.path.join(temp_folder, file_name + '.zip')
    # Set a file path to move the .zip file to the target folder
    target_zip_file = os.path.join(target_folder, file_name + '.zip')

    # # Capture vtk files in a zip file.
    cur_dir = os.path.abspath(os.path.curdir)
    zipobj = ZipFile(temp_zip_file, 'w')
    os.chdir(temp_folder)
    for name in file_names:
        name = os.path.join(name + vtk_extension)
        zipobj.write(name)
    zipobj.close()
    os.chdir(target_folder)

    # Move the generated HTML to target folder
    shutil.move(temp_zip_file, target_zip_file)

    # Remove temp folder
    shutil.rmtree(temp_folder)

    # change back to original folder
    os.chdir(cur_dir)

    # Return the path where the .zip file is written
    return target_zip_file


def write_html(hbjson, file_path, file_name, target_folder, open_html, include_grids,
               include_sensors, include_normals):
    """Write an HTML file with VTK objects embedded into it.

    Args:
        hbjson: A dictionary.
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
            'vectors' and 'points.' Defaults to False.
        include_normals: A text string to indicate whether to show face normals as
            vectors or points colored based on directions. Acceptable values are;
            'vectors' and 'points.' Defaults to False. Currently, this function
            only exports normals for the apertures. Other face types will be supported
            in future.

    Returns:
        A text string containing the path to the HTML file with VTK objects embedded.
    """
    # Path to the Paraview Glance template
    html_path = pathlib.Path(pathlib.Path(__file__).parent, 'assets/ParaViewGlance.html')

    # Make sure the template if found
    if not os.path.exists(html_path):
        raise FileNotFoundError('Paraview Glance HTML template not found.')

    # Create a temp folder
    temp_folder = tempfile.mkdtemp()

    # Setting DataSet Writer and file extension
    vtk_writer = vtk.vtkJSONDataSetWriter()
    vtk_extension = ""

    file_names = _write(
        hbjson, temp_folder, vtk_writer, vtk_extension, include_grids, include_sensors,
        include_normals)

    # Write index.json
    write_index_json(temp_folder, file_names)

    # Use the name of HBJSON if file name is not provided
    if not file_name:
        name = '.'.join(os.path.basename(file_path).split('.')[:-1])
        file_name = clean_string(name)

    # remove extension if provided by user
    file_name = file_name if not file_name.lower().endswith('.zip') else file_name[:-4]

    # Create a .zip file to capture all the generated json dataset folders
    file_path = os.path.join(temp_folder, file_name)
    shutil.make_archive(file_path, 'zip', temp_folder)

    # Setting file paths
    zip_file = os.path.join(temp_folder, file_name + '.zip')
    vtkjs_file = os.path.join(temp_folder, file_name + '.vtkjs')
    temp_html_file = os.path.join(temp_folder, file_name + '.html')
    target_html_file = os.path.join(target_folder, file_name + '.html')

    # Renaming .zip to .vtkjs
    os.rename(zip_file, vtkjs_file)

    # Embed json datasets in HTML
    convert_directory_to_zip_file(vtkjs_file)
    add_data_to_viewer(vtkjs_file, html_path)

    # Move the generated HTML to target folder
    shutil.move(temp_html_file, target_html_file)

    # Remove temp folder
    shutil.rmtree(temp_folder)

    # Open the generated HTML in a browser if requested
    if open_html:
        webbrowser.open(target_html_file)

    return target_html_file
