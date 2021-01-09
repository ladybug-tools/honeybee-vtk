"""Write vtk files to the disk."""

import os
import json
import vtk
import warnings

from zipfile import ZipFile
from .hbjson import read_hbjson, get_grid, get_grid_mesh, get_mesh, get_joined_face_vertices, get_face_center
from .tovtk import create_polygons, group_by_face_type, create_arrows
from .tovtk import point_vectors, create_cones, create_mesh


def write_vtk(file_path):
    """Read a valid HBJSON and write a vtk file to disk.

    Args:
        file_path: A text string for a valid path to the HBJSON file.
    """
    # HBJSON file
    if file_path:
        # Check if path is fine
        if not os.path.isfile(file_path):
            raise FileNotFoundError(
                'The path is not a valid path.'
                ' If file exists, try using double backslashes in file path'
                ' and try again.'
            )
    try:
        # Check if the file is a valid JSON
        with open(file_path) as fp:
            hbjson = json.load(fp)
    except json.decoder.JSONDecodeError:
        raise ValueError(
            'Not a valid JSON file.'
            )
    else:
        # Get points and face_types from HBJSON
        points_lst, hb_types, display_names = read_hbjson(hbjson)

        # Get points grouped for each Honeybee face_type
        grouped_points, grouped_display_names = group_by_face_type(points_lst, display_names, hb_types)

        for hb_type in grouped_points:
            # Get vtk polygons
            vtk_polydata_extended = create_polygons(grouped_points[hb_type],
                grouped_display_names[hb_type])
            
            # Write faces to vtk
            writer = vtk.vtkPolyDataWriter()
            writer.SetFileName(hb_type + '.vtk')
            writer.SetInputConnection(vtk_polydata_extended.GetOutputPort())
            writer.Write()

        file_names = list(grouped_points.keys())

        # Create face normals
        start_points, end_points, normals = get_face_center(points_lst)
        face_vector_polydata = create_arrows(start_points, end_points, normals)
        writer = vtk.vtkPolyDataWriter()
        writer.SetFileName('face vectors.vtk')
        writer.SetInputConnection(face_vector_polydata.GetOutputPort())
        writer.Write()
        file_names.append('face vectors')

        # write grid points to a vtk file
        if get_grid(hbjson):
            # mesh_points, mesh_faces = get_mesh(hbjson)
            # create_polyhedron(mesh_points, mesh_faces)

            start_points, end_points, vectors  = get_grid(hbjson)
            point_polydata = point_vectors(start_points, vectors)
            writer = vtk.vtkPolyDataWriter()
            writer.SetFileName('grid points.vtk')
            # writer.SetInputConnection(grid_polydata_extended.GetOutputPort())
            writer.SetInputData(point_polydata)
            writer.Write()
            file_names.append('grid points')
        else:
            pass

        # Capture vtk files in a zip file.
        zipobj = ZipFile('unnamed.zip', 'w')
        for file_name in file_names:
            zipobj.write(file_name + '.vtk')
        zipobj.close()

        # Delete vtk files if permitted
        for file_name in file_names:
            try:
                os.remove(file_name + '.vtk')
            except OSError:
                warnings.warn(
                    'Honeybee does not have permission to delete files. You can delete' 
                    ' the .vtk files manually.'
                )
