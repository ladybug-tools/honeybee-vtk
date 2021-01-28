"""A collection of functions to write VTK objects to file."""


import os

from typing import List
from .to_vtk import create_polygons, create_points, create_arrows, \
    create_color_grouped_points
from .helper import get_end_point, get_vector_at_center, get_point3d, get_vector3d
from .hbjson import get_grid_base, get_grid_mesh, get_grid_points


def write_polydata(
        grouped_points, file_name, vtk_writer, vtk_extension, target_folder):
    """Write VTK Polydata to a file.

    Args:
        grouped_points: A dictionary with Honeybee type as keys and list of
        lists of Point3Ds for geometry that belongs to that Honeybee type.
        An example would be;

        .. code-block:: python

            {
            'Wall': [[Point1, Point2, Point3], [Point4, Point5, Point6, Point7]],
            'Aperture': [[Point1, Point2, Point3], [Point4, Point5, Point6, Point7]]
            }

        file_name: A text string for the the file name to be written.
        vtk_writer: A vtk object. Acceptable values are following;
            vtk.vtkXMLPolyDataWriter(), vtk.vtkPolyDataWriter(), and
            vtk.vtkJSONDataSetWriter() to write XML, VTK, and HTML files respectively.
        vtk_extension: A text string for the file extension to be used. Following are
            acceptable values for the corresponding vtk_writer values;
            '.vtk', '.vtp', ''.
            Please note that the vtk_extension value is a an empty string with no spaces
            in the case of vtk_writer having the value of 'html'.
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


def write_points(
        points: List[List], vectors: List[List], *, file_name, target_folder,
        vtk_writer, vtk_extension):
    """Write VTK points to a file.

    Args:
        points : A list of lists. Here, each list has X, Y, and Z coordinates of a point.
        vectors: A list of lists. Here, each list has X, Y, and Z components of a vector.
        file_name: A text string to be used as a file name.
        target_folder: A text string to a folder to write the output vtk file.
        vtk_writer: A vtk object. Acceptable values are following;
            vtk.vtkXMLPolyDataWriter(), vtk.vtkPolyDataWriter(), and
            vtk.vtkJSONDataSetWriter() to write XML, VTK, and HTML files respectively.
        vtk_extension: A text string for the file extension to be used. Following are
            acceptable values for the corresponding vtk_writer values;
            '.vtk', '.vtp', ''.
            Please note that the vtk_extension value is a an empty string with no spaces
            in the case of vtk_writer having the value of 'html'.
        
    Returns:
        A text string containing the path to the file.
    """
    file_name = file_name + vtk_extension
    if not vectors:
        point_polydata = create_points(points)
    else:
        point_polydata = create_color_grouped_points(points, vectors)
    writer = vtk_writer
    file_name = os.path.join(target_folder, file_name)
    writer.SetFileName(file_name)
    writer.SetInputData(point_polydata)
    writer.Write()

    return file_name


def write_arrows(start_points, vectors, *, file_name, target_folder, vtk_writer,
                 vtk_extension):
    """Write VTK arrows to a file.

    Args:
        start_points: A list Ladybug Point3D objects.
        vectors: A list of Ladybug Vector3D objects.
        file_name: A text string to be used as the file name.
        target_folder: A text string to a folder to write the output file. The file
            will be written to the current folder if not provided.
        vtk_writer: A vtk object. Acceptable values are following;
            vtk.vtkXMLPolyDataWriter(), vtk.vtkPolyDataWriter(), and
            vtk.vtkJSONDataSetWriter() to write XML, VTK, and HTML files respectively.
        vtk_extension: A text string for the file extension to be used. Following are
            acceptable values for the corresponding vtk_writer values;
            '.vtk', '.vtp', ''.
            Please note that the vtk_extension value is a an empty string with no spaces
            in the case of vtk_writer having the value of 'html'. 

    Returns:
        A text string containing the path to the file.
    """
    end_points = [
        get_end_point(point, vector)
        for point, vector in zip(start_points, vectors)]

    file_name = file_name + vtk_extension
    face_vector_polydata = create_arrows(start_points, end_points, vectors)
    writer = vtk_writer
    file_name = os.path.join(target_folder, file_name)
    writer.SetFileName(file_name)
    writer.SetInputConnection(face_vector_polydata.GetOutputPort())
    writer.Write()

    return file_name


def _write_grids(grids, vtk_writer, vtk_extension, target_folder, include_sensors):
    """
    Write HBJSON Sensorgrid objects to file.

    Args:
        grids: A tuple of following three lists.
            A list of HBJSON sensorgrids that have 'base_geometry' as a key.
            A list of HBJSON sensorgrids that have 'mesh' as a key and does not have
            'base_geometry' as a key.
            A list of HBJSON sensorgrids that have neither 'mesh' nor 'base_geometry'
            as keys.
        vtk_writer: A vtk object. Acceptable values are following;
            vtk.vtkXMLPolyDataWriter(), vtk.vtkPolyDataWriter(), and
            vtk.vtkJSONDataSetWriter() to write XML, VTK, and HTML files respectively.
        vtk_extension: A text string for the file extension to be used. Following are
            acceptable values for the corresponding vtk_writer values;
            '.vtk', '.vtp', ''.
            Please note that the vtk_extension value is a an empty string with no spaces
            in the case of vtk_writer having the value of 'html'.
        target_folder: A text string to a folder to write the output vtk file.
        include_sensors: A text string to indicate whether to show sensor directions as
            vectors or points colored based on directions. Acceptable values are;
            'vectors' and 'points.' Defaults to False.

    Returns:
        A list of strings for file names.
    """
    grid_file_names = []

    # If base_geometry is found
    if grids[0]:
        base_geo_points = get_grid_base(grids[0])[0]
        write_polydata(base_geo_points, 'Grid base', vtk_writer, vtk_extension,
                       target_folder)
        grid_file_names.append('Grid base')

    # If base_geometry is not found but mesh faces are found
    if grids[1]:
        mesh_points = get_grid_mesh(grids[1])[0]
        write_polydata(mesh_points, 'Grid mesh', vtk_writer, vtk_extension,
                       target_folder)
        grid_file_names.append('Grid mesh')

    # If only grid points are found
    if grids[2] and include_sensors != 'points':
        start_points = get_grid_points(grids[2])[0]
        vectors = None
        write_points(start_points, vectors, 'Grid points', target_folder, vtk_writer,
                     vtk_extension)
        grid_file_names.append('Grid points')

    return grid_file_names


def _write_sensors(include_sensors, grids, vtk_writer, vtk_extension, target_folder):
    """
    Write points that are color-grouped based on the direction of vectors.

    Args:
        include_sensors: Bool value of False or a value from 'vectors' or 'points.'
        grids: A of following three lists.
            A list of HBJSON sensorgrids that have 'base_geometry' as a key.
            A list of HBJSON sensorgrids that have 'mesh' as a key and does not have
            'base_geometry' as a key.
            A list of HBJSON sensorgrids that have neither 'mesh' nor 'base_geometry'
            as keys.
        vtk_writer: A vtk object. Acceptable values are following;
            vtk.vtkXMLPolyDataWriter(), vtk.vtkPolyDataWriter(), and
            vtk.vtkJSONDataSetWriter() to write XML, VTK, and HTML files respectively.
        vtk_extension: A text string for the file extension to be used. Following are
            acceptable values for the corresponding vtk_writer values;
            '.vtk', '.vtp', ''.
            Please note that the vtk_extension value is a an empty string with no spaces
            in the case of vtk_writer having the value of 'html'.
        target_folder: A text string to a folder to write the output vtk file. 

    Returns:
        A list of strings for file names.
    """
    if include_sensors == 'vectors':
        sensor_writer = write_arrows
        layer_name_extension = 'vectors'
    else:
        sensor_writer = write_points
        layer_name_extension = 'points'

    sensor_file_names = []

    # If base_geometry is found in any of the grids
    if grids[0]:
        grid_points, grid_vectors = get_grid_points(grids[0])
        start_points = get_point3d(grid_points)
        vectors = get_vector3d(grid_vectors)
        layer_name = 'Grid base ' + layer_name_extension
        sensor_writer(
            start_points, vectors, file_name=layer_name, target_folder=target_folder,
            vtk_writer=vtk_writer, vtk_extension=vtk_extension)
        sensor_file_names.append(layer_name)

    # If mesh is found in any of the grids
    if grids[1]:
        mesh_points = get_grid_mesh(grids[1])[0]
        start_points, vectors = get_vector_at_center(mesh_points)
        layer_name = 'Grid mesh ' + layer_name_extension
        sensor_writer(
            start_points, vectors, file_name=layer_name, target_folder=target_folder,
            vtk_writer=vtk_writer, vtk_extension=vtk_extension)
        sensor_file_names.append(layer_name)

    # If only grid points and vectors are there in the grids
    if grids[2]:
        grid_points, grid_vectors = get_grid_points(grids[2])
        start_points = get_point3d(grid_points)
        vectors = get_vector3d(grid_vectors)
        if layer_name_extension == 'points':
            layer_name = 'Grid points'
        else:
            layer_name = 'Grid points ' + layer_name_extension
        sensor_writer(
            start_points, vectors, file_name=layer_name, target_folder=target_folder,
            vtk_writer=vtk_writer, vtk_extension=vtk_extension)

    return sensor_file_names


def _write_normals(include_normals, hb_types, grouped_points, vtk_writer, vtk_extension,
                   target_folder):
    """
    Write face normals as either arrows or color-grouped points.

    Currently, this function only writes face normals for apertures.

    Args:
        include_normals: A text string to indicate whether to show face normals as
            vectors or points colored based on directions. Acceptable values are;
            'vectors' and 'points.' Defaults to False. Currently, this function
            only exports normals for the apertures. Other face types will be supported
            in future.
        hb_types: A list of text strings. Each text string represents either the
            Honeybee face type or the Honeybee face object for each list of Point3Ds
            in points.
        grouped_points: A dictionary with Honeybee type as keys and list of lists of
            Point3Ds for geometry that belongs to that Honeybee type. An example would
            be;

            .. code-block:: python

                {
                'Wall': [[Point1, Point2, Point3], [Point4, Point5, Point6, Point7]],
                'Aperture': [[Point1, Point2, Point3], [Point4, Point5, Point6, Point7]]
                }
                
        vtk_writer: A vtk object. Acceptable values are following;
            vtk.vtkXMLPolyDataWriter(), vtk.vtkPolyDataWriter(), and
            vtk.vtkJSONDataSetWriter() to write XML, VTK, and HTML files respectively.
        vtk_extension: A text string for the file extension to be used. Following are
            acceptable values for the corresponding vtk_writer values;
            '.vtk', '.vtp', ''.
            Please note that the vtk_extension value is a an empty string with no spaces
            in the case of vtk_writer having the value of 'html'.
        target_folder: A text string to a folder to write the output vtk file.

    Returns:
        A list of strings for file names.
    """
    normal_file_names = []

    # Create face normals
    start_points, vectors = get_vector_at_center(grouped_points['Aperture'])

    if include_normals == 'vectors':
        write_arrows(
            start_points, vectors, file_name='Aperture vectors',
            target_folder=target_folder, vtk_writer=vtk_writer,
            vtk_extension=vtk_extension)
        normal_file_names.append('Aperture vectors')

    elif include_normals == 'points':
        write_points(
            start_points, vectors, file_name='Aperture points',
            target_folder=target_folder, vtk_writer=vtk_writer,
            vtk_extension=vtk_extension)
        normal_file_names.append('Aperture points')

    return normal_file_names
