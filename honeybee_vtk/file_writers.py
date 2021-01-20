"""Functions to write vtk/vtp or HTML files using vtk."""

import os
import vtk
import warnings
import shutil
import webbrowser

from zipfile import ZipFile
from honeybee.typing import clean_string
from .hbjson import check_grid, read_hbjson, group_by_face_type
from .writers import write_polydata, _write_grids, _write_vectors
from .index import write_index_json
from .vtkjs_helper import convertDirectoryToZipFile, addDataToViewer


def write_files(file_path, file_name, target_folder, include_grids,
                include_vectors, vtk_writer, vtk_extension, hbjson):
    """
    Write a .zip of VTK/VTP files.

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
        vtk_writer: A VTK writer object.
        vtk_extension: A text string for the file extension to be used.
        hbjson: A dictionary.

    Returns:
        A text string containing the path to the .zip file with VTK/VTP files.
    """
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
    os.chdir(target_folder)
    for file_name in file_names:
        zipobj.write(file_name + vtk_extension)
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


def write_html(file_path, file_name, target_folder, include_grids, include_vectors,
               hbjson):
    """Write an HTML file with VTK objects embedded into it.

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
        vtk_writer: A VTK writer object.
        vtk_extension: A text string for the file extension to be used.
        hbjson: A dictionary.

    Returns:
        A text string containing the path to the HTML file with VTK objects embedded.
    """

    # Create a new folder at target folder to store all the files
    folder_name = 'hbjson-html'
    target_folder = os.path.join(target_folder, folder_name)
    if os.path.exists(target_folder):
        shutil.rmtree(target_folder)

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

    # Write index.json
    write_index_json(target_folder, file_names)

    # Collect everything in a .zip
    # Use the name of HBJSON if file name is not provided
    if not file_name:
        name = '.'.join(os.path.basename(file_path).split('.')[:-1])
        file_name = clean_string(name)

    # remove extension if provided by user
    file_name = file_name if not file_name.lower().endswith('.zip') else file_name[:-4]

    # Create a .zip file to capture all the generated .vtk files
    zip_name = file_name
    file_path = os.path.join(target_folder, file_name)
    shutil.make_archive(file_path, 'zip', target_folder)
 
    # Delete the index.json if there is permission
    try:
        file_name = os.path.join(target_folder, 'index.json')
        os.remove(file_name)
    except OSError:
        warnings.warn(
            'Honeybee does not have permission to delete index.json.'
            ' You may please delete the .vtk files manually.'
        )
    # Delete the folders containing json datasets if there is permission
    for file_name in file_names:
        try:
            file_name = os.path.join(target_folder, file_name)
            shutil.rmtree(file_name)
        except OSError:
            warnings.warn(
                f'Honeybee does not have permission to delete {file_names}.'
                ' You may please delete the .vtk files manually.'
            )
    
    # Setting file names for three different formats
    zip_file = os.path.join(target_folder, zip_name + '.zip')
    vtkjs_file = os.path.join(target_folder, zip_name + '.vtkjs')
    html_file = os.path.join(target_folder, zip_name + '.html')

    # Renaming .zip to .vtkjs
    os.rename(zip_file, vtkjs_file)

    # Path to the Paraview Glance template
    html_path = '../honeybee-vtk/Paraview Glance/ParaViewGlance.html'

    # Embed json datasets in HTML
    if os.path.exists(html_path):
        convertDirectoryToZipFile(vtkjs_file)
        addDataToViewer(vtkjs_file, html_path)
    
    # Delete vtkjs file
    try:
        os.remove(vtkjs_file)
    except OSError:
        warnings.warn(
            'Honeybee does not have permission to delete index.json.'
            ' You may please delete the .vtk files manually.'
        )
    
    webbrowser.open(html_file)

    # File path to the HTML file
    return html_file
    
