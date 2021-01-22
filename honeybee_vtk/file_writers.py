"""Functions to write vtk, vtp or HTML files using vtk."""

import os
import vtk
import shutil
import tempfile
import webbrowser
import pathlib

from zipfile import ZipFile
from honeybee.typing import clean_string
from .hbjson import check_grid, read_hbjson, group_by_face_type
from .writers import write_polydata, _write_grids, _write_vectors, _write_points
from .index import write_index_json
from .vtkjs_helper import convert_directory_to_zip_file, add_data_to_viewer


def write_files(hbjson, file_path, file_name, target_folder, include_grids,
                include_vectors, include_points, vtk_writer, vtk_extension):
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
        include_vectors: A boolean. Defaults to True. Vector arrows will not be created
            if set to False.
        include_points: A boolean. Defaults to False. If set to True, sensor points
            color-grouped based on their vector direction will be exported instead of
            arrows for the vectors.
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
    grids = check_grid(hbjson)

    # If grids are there in HBJSON and they are requested
    if grids and include_grids:
        grid_file_names = _write_grids(
            grids, vtk_writer, vtk_extension, temp_folder, include_points)
        file_names.extend(grid_file_names)

    # Write vectors if they are requested
    if include_vectors:
        vector_file_names = _write_vectors(
            hb_types, grouped_points, grids, include_grids, vtk_writer, vtk_extension,
            temp_folder)
        file_names.extend(vector_file_names)
    
    # Write color-grouped points if they are requested
    if include_points:
        point_file_names = _write_points(
            hb_types, grouped_points, grids, include_grids, vtk_writer, vtk_extension,
            temp_folder)
        file_names.extend(point_file_names)

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


def write_html(hbjson, file_path, file_name, target_folder, include_grids,
               include_vectors, include_points, open_html):
    """Write an HTML file with VTK objects embedded into it.

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
        include_vectors: A boolean. Defaults to True. Vector arrows will not be created
            if set to False.
        include_points: A boolean. Defaults to False. If set to True, sensor points
            color-grouped based on their vector direction will be exported instead of
            arrows for the vectors.
        open_html: A boolean. If set to False, it will not open the generated HTML
            in a web browser.

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
    grids = check_grid(hbjson)

    # If grids are there in HBJSON and they are requested
    if grids and include_grids:
        grid_file_names = _write_grids(
            grids, vtk_writer, vtk_extension, temp_folder, include_points)
        file_names.extend(grid_file_names)

    # Write vectors if they are requested
    if include_vectors:
        vector_file_names = _write_vectors(
            hb_types, grouped_points, grids, include_grids, vtk_writer, vtk_extension,
            temp_folder)
        file_names.extend(vector_file_names)
    
    # Write color-grouped points if they are requested
    if include_points:
        point_file_names = _write_points(
            hb_types, grouped_points, grids, include_grids, vtk_writer, vtk_extension,
            temp_folder)
        file_names.extend(point_file_names)

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
