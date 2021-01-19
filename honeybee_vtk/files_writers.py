"""A collection of helper functions to write VTK to file."""

import vtk
import os

from zipfile import ZipFile
from honeybee.typing import clean_string
from typing import List
from .to_vtk import create_polygons, point_vectors, create_arrows
from .helper import get_end_point, get_vector_at_center
from .hbjson import get_grid_base, get_grid_mesh, get_grid_points
from .hbjson import check_grid, read_hbjson, group_by_face_type


def write_polydata(
        grouped_points, file_name, vtk_writer, vtk_extension, target_folder):
    """Write VTK Polydata to a file.

    Args:
        grouped_points: A dictionary with Honeybee type as keys and list of 
        lists of Point3Ds for geometry that belongs to that Honeybee type. 
        An example would be;
        {
        'Wall': [[Point1, Point2, Point3], [Point4, Point5, Point6, Point7]],
        'Aperture': [[Point1, Point2, Point3], [Point4, Point5, Point6, Point7]]
        }
        file_name: A text string for the the file name to be written.
        vtk_writer: A text string to indicate the VTK writer. Acceptable values are
            'vtk' and 'xml'.
        vtk_extension: A text string that indicates file extension for the files to be
            written. This will be '.vtk' for vtk writer and '.vtp' for xml writer.
        target_folder: A text string to a folder to write the output vtk file. 

    Returns:
        A text string containing the path to the file.
    """
    file_name = file_name + vtk_extension
    vtk_polydata_extended = create_polygons(grouped_points)
    writer = vtk_writer
    file_name = os.path.join(target_folder, file_name)
    writer.SetFileName(file_name)
    writer.SetInputConnection(vtk_polydata_extended.GetOutputPort())
    writer.Write()

    return file_name


def write_color_grouped_points(
        points: List[List], vectors: List[List], vtk_writer, vtk_extension,
        target_folder, file_name='grid points'):
    """Write color-grouped VTK points to a file.

    Args:
        points : A list of lists. Here, each list has X, Y, and Z coordinates of a point.
        vectors: A list of lists. Here, each list has X, Y, and Z components of a vector.
        vtk_writer: A text string to indicate the VTK writer. Acceptable values are
            'vtk' and 'xml'.
        vtk_extension: A text string that indicates file extension for the files to be
            written. This will be '.vtk' for vtk writer and '.vtp' for xml writer.
        target_folder: A text string to a folder to write the output vtk file. 
        file_name: A text string to be used as a file name. Defaults to "grid points."

    Returns:
        A text string containing the path to the file.
    """
    file_name = file_name + vtk_extension
    point_polydata = point_vectors(points, vectors)
    writer = vtk_writer
    file_name = os.path.join(target_folder, file_name)
    writer.SetFileName(file_name)
    writer.SetInputData(point_polydata)
    writer.Write()

    return file_name


def write_arrows(
    start_points, vectors, file_name, target_folder, vtk_writer=vtk.vtkPolyDataWriter(),
        vtk_extension='.vtk'):
    """Write VTK arrows to a file.

    Args:
        start_points: A list Ladybug Point3D objects.
        vectors: A list of Ladybug Vector3D objects.
        file_name: A text string to be used as the file name.
        target_folder: A text string to a folder to write the output file. The file
            will be written to the current folder if not provided.
        vtk_writer: A text string to indicate the VTK writer. Acceptable values are
            'vtk' and 'xml'.
        vtk_extension: A text string to a folder to write the output vtk file. 

    Returns:
        A text string containing the path to the file.
    """
    end_points = [
        get_end_point(point, vector)
        for point, vector in zip(start_points, vectors)]

    file_name = file_name + ' vectors' + vtk_extension
    face_vector_polydata = create_arrows(start_points, end_points, vectors)
    writer = vtk_writer
    file_name = os.path.join(target_folder, file_name)
    writer.SetFileName(file_name)
    writer.SetInputConnection(face_vector_polydata.GetOutputPort())
    writer.Write()
    
    return file_name


def _write_grids(grids, vtk_writer, vtk_extension, target_folder):
    """
    Write HBJSON Sensorgrid objects to file.

    Args:
        grids: A of following three lists.
            A list of HBJSON sensorgrids that have 'base_geometry' as a key.
            A list of HBJSON sensorgrids that have 'mesh' as a key and does not have
            'base_geometry' as a key.
            A list of HBJSON sensorgrids that have neither 'mesh' nor 'base_geometry'
            as keys.
        vtk_writer: A text string to indicate the VTK writer. Acceptable values are
            'vtk' and 'xml'.
        vtk_extension: A text string that indicates file extension for the files to be
            written. This will be '.vtk' for vtk writer and '.vtp' for xml writer.
        target_folder: A text string to a folder to write the output vtk file. 

    Returns:
        A list of strings for file names.
    """
    grid_file_names = []

    # If base_geometry is found
    if grids[0]:
        base_geo_points = get_grid_base(grids[0])[0]
        write_polydata(base_geo_points, 'grid base', vtk_writer, vtk_extension,
                       target_folder)
        grid_file_names.append('grid base')

    # If base_geometry is not found but mesh faces are found
    if grids[1]:
        mesh_points = get_grid_mesh(grids[1])[0]
        write_polydata(mesh_points, 'grid mesh', vtk_writer, vtk_extension,
                       target_folder)
        grid_file_names.append('grid mesh')

    # If only grid points are found
    if grids[2]:
        start_points, vectors = get_grid_points(grids[2])
        write_color_grouped_points(start_points, vectors, vtk_writer, vtk_extension,
                                   target_folder)
        grid_file_names.append('grid points')

    return grid_file_names


def _write_vectors(hb_types, grouped_points, grids, include_grids, vtk_writer,
                   vtk_extension, target_folder):
    """
    Write vectors to file.

    Args:
        hb_types: A list of text strings. Each text string represents either the
            Honeybee face type or the Honeybee face object for each list of Point3Ds
            in points.
        grouped_points: A dictionary with Honeybee type as keys and list of lists of
            Point3Ds for geometry that belongs to that Honeybee type. An example would
            be;
            {
            'Wall': [[Point1, Point2, Point3], [Point4, Point5, Point6, Point7]],
            'Aperture': [[Point1, Point2, Point3], [Point4, Point5, Point6, Point7]]
            }
        grids: A of following three lists.
            A list of HBJSON sensorgrids that have 'base_geometry' as a key.
            A list of HBJSON sensorgrids that have 'mesh' as a key and does not have
            'base_geometry' as a key.
            A list of HBJSON sensorgrids that have neither 'mesh' nor 'base_geometry'
            as keys.
        include_grids: A boolean. Grids will be included if the value is True.
        vtk_writer: A text string to indicate the VTK writer. Acceptable values are
            'vtk' and 'xml'.
        vtk_extension: A text string that indicates file extension for the files to be
            written. This will be '.vtk' for vtk writer and '.vtp' for xml writer.
        target_folder: A text string to a folder to write the output vtk file. 

    Returns:
        A list of strings for file names.
    """
    vector_file_names = []

    # If Aperture objects are there in HBJSON
    if 'Aperture' in hb_types:
        # Create face normals
        start_points, vectors = get_vector_at_center(
            grouped_points['Aperture'])
        write_arrows(start_points, vectors, 'Aperture', target_folder, vtk_writer,
                     vtk_extension)
        vector_file_names.append('Aperture vectors')

    # If grids are found in HBJSON
    if grids and include_grids:

        # If base_geometry is found in any of the grids
        if grids[0]:
            base_geo_points = get_grid_base(grids[0])[0]
            start_points, vectors = get_vector_at_center(base_geo_points)
            write_arrows(start_points, vectors, 'grid base', target_folder, vtk_writer,
                         vtk_extension)
            vector_file_names.append('grid base vectors')

        # If mesh is found in any of the grids
        if grids[1]:
            mesh_points = get_grid_mesh(grids[1])[0]
            start_points, vectors = get_vector_at_center(mesh_points)
            write_arrows(start_points, vectors, 'grid mesh', target_folder, vtk_writer,
                         vtk_extension)
            vector_file_names.append('grid mesh vectors')

    return vector_file_names


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
