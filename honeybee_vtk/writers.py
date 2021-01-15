"""A collection of helper functions to write VTK to file."""

import vtk
import os

from typing import List
from .to_vtk import create_polygons, point_vectors, create_arrows
from .helper import get_end_point, get_vector_at_center
from .hbjson import get_grid_base, get_grid_mesh, get_grid_points


def write_polydata(
        polydata, file_name, vtk_writer, vtk_extension):
    """Write VTK Polydata to a file.

    Args:
        polydata: An appended VTK polydata object.
        file_name: A text string for the the file name to be written.
        vtk_writer: A text string to indicate the VTK writer. Acceptable values are
            'vtk' and 'xml'.
        vtk_extension: A text string that indicates file extension for the files to be
            written. This will be '.vtk' for vtk writer and '.vtp' for xml writer.

    Returns:
        A text string containing the path to the file.
    """
    file_name = file_name + vtk_extension
    vtk_polydata_extended = create_polygons(polydata)
    writer = vtk_writer
    writer.SetFileName(file_name)
    writer.SetInputConnection(vtk_polydata_extended.GetOutputPort())
    writer.Write()
    return os.path.join(os.getcwd(), file_name)


def write_color_grouped_points(
        points: List[List], vectors: List[List], vtk_writer, vtk_extension,
        file_name='grid points'):
    """Write color-grouped VTK points to a file.

    Args:
        points : A list of lists. Here, each list has X, Y, and Z coordinates of a point.
        vectors: A list of lists. Here, each list has X, Y, and Z components of a vector.
        vtk_writer: A text string to indicate the VTK writer. Acceptable values are
            'vtk' and 'xml'.
        vtk_extension: A text string that indicates file extension for the files to be
            written. This will be '.vtk' for vtk writer and '.vtp' for xml writer.
        file_name: A text string to be used as a file name. Defaults to "grid points."

    Returns:
        A text string containing the path to the file.
    """
    file_name = file_name + vtk_extension
    point_polydata = point_vectors(points, vectors)
    writer = vtk_writer
    writer.SetFileName(file_name)
    writer.SetInputData(point_polydata)
    writer.Write()
    return os.path.join(os.getcwd(), file_name)


def write_arrows(
    start_points, vectors, file_name, vtk_writer=vtk.vtkPolyDataWriter(),
        vtk_extension='.vtk'):
    """Write VTK arrows to a file.

    Args:
        start_points: A list Ladybug Point3D objects.
        vectors: A list of Ladybug Vector3D objects.
        file_name: A text string to be used as the file name.
        vtk_writer: A text string to indicate the VTK writer. Acceptable values are
            'vtk' and 'xml'.
        vtk_extension: A text string that indicates file extension for the files to be
            written. This will be '.vtk' for vtk writer and '.vtp' for xml writer.

    Returns:
        A text string containing the path to the file.
    """
    end_points = [
        get_end_point(point, vector)
        for point, vector in zip(start_points, vectors)]

    file_name = file_name + ' vectors' + vtk_extension
    face_vector_polydata = create_arrows(start_points, end_points, vectors)
    writer = vtk_writer
    writer.SetFileName(file_name)
    writer.SetInputConnection(face_vector_polydata.GetOutputPort())
    writer.Write()
    return os.path.join(os.getcwd(), file_name)


def _write_grids(grids, vtk_writer, vtk_extension):
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

    Returns:
        A list of strings for file names.
    """
    grid_file_names = []

    # If base_geometry is found
    if grids[0]:
        base_geo_points = get_grid_base(grids[0])[0]
        write_polydata(base_geo_points, 'grid base', vtk_writer, vtk_extension)
        grid_file_names.append('grid base')

    # If base_geometry is not found but mesh faces are found
    if grids[1]:
        mesh_points = get_grid_mesh(grids[1])[0]
        write_polydata(mesh_points, 'grid mesh', vtk_writer, vtk_extension)
        grid_file_names.append('grid mesh')

    # If only grid points are found
    if grids[2]:
        start_points, vectors = get_grid_points(grids[2])
        write_color_grouped_points(start_points, vectors, vtk_writer, vtk_extension)
        grid_file_names.append('grid points')

    return grid_file_names


def _write_vectors(hb_types, grouped_points, grids, include_grids, vtk_writer,
                   vtk_extension):
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

    Returns:
        A list of strings for file names.
    """
    vector_file_names = []

    # If Aperture objects are there in HBJSON
    if 'Aperture' in hb_types:
        # Create face normals
        start_points, vectors = get_vector_at_center(
            grouped_points['Aperture'])
        write_arrows(start_points, vectors, 'Aperture', vtk_writer, vtk_extension)
        vector_file_names.append('Aperture vectors')

    # If grids are found in HBJSON
    if grids and include_grids:

        # If base_geometry is found in any of the grids
        if grids[0]:
            base_geo_points = get_grid_base(grids[0])[0]
            start_points, vectors = get_vector_at_center(base_geo_points)
            write_arrows(start_points, vectors, 'grid base', vtk_writer, vtk_extension)
            vector_file_names.append('grid base vectors')

        # If mesh is found in any of the grids
        if grids[1]:
            mesh_points = get_grid_mesh(grids[1])[0]
            start_points, vectors = get_vector_at_center(mesh_points)
            write_arrows(start_points, vectors, 'grid mesh', vtk_writer, vtk_extension)
            vector_file_names.append('grid mesh vectors')

    return vector_file_names
