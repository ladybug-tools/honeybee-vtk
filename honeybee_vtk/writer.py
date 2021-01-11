"""Write vtk files to the disk."""

import os
import json
import vtk
import warnings

from zipfile import ZipFile
from .hbjson import read_hbjson, get_face_center
from .hbjson import check_grid, get_grid_base, get_grid_mesh, get_grid_points
from .tovtk import create_polygons, group_by_face_type, create_arrows
from .tovtk import point_vectors
from .helper import get_point3d


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
        points_lst, hb_types = read_hbjson(hbjson)

        # Get points grouped for each Honeybee face_type
        grouped_points = group_by_face_type(points_lst, hb_types)

        for hb_type in grouped_points:
            # Get vtk polygons
            vtk_polydata_extended = create_polygons(grouped_points[hb_type])
            # Write faces to vtk
            writer = vtk.vtkPolyDataWriter()
            writer.SetFileName(hb_type + '.vtk')
            writer.SetInputConnection(vtk_polydata_extended.GetOutputPort())
            writer.Write()

        file_names = list(grouped_points.keys())



        # write grid points to a vtk file
        grids = check_grid(hbjson)

        # If grids are there in HBJSON
        if grids:

            # If base_geometry is found
            if grids[0]:
                base_geo_points = get_grid_base(grids[0])[0]
                vtk_polydata_extended = create_polygons(base_geo_points)
                # Write faces to vtk
                writer = vtk.vtkPolyDataWriter()
                writer.SetFileName('grid base.vtk')
                writer.SetInputConnection(vtk_polydata_extended.GetOutputPort())
                writer.Write()
                file_names.append('grid base')

            # If base_geometry is not found but mesh faces are found
            if grids[1]:
                mesh_points = get_grid_mesh(grids[1])[0]
                vtk_polydata_extended = create_polygons(mesh_points)
                # Write faces to vtk
                writer = vtk.vtkPolyDataWriter()
                writer.SetFileName('grid mesh.vtk')
                writer.SetInputConnection(vtk_polydata_extended.GetOutputPort())
                writer.Write()
                file_names.append('grid mesh')

            # If only grid points are found
            if grids[2]:
                start_points, end_points, vectors = get_grid_points(grids[2])
                point_polydata = point_vectors(start_points, vectors)
                writer = vtk.vtkPolyDataWriter()
                writer.SetFileName('grid points.vtk')
                writer.SetInputData(point_polydata)
                writer.Write()
                file_names.append('grid points')
        else:
            pass
        
        if 'Aperture' in hb_types:
            # Create face normals
            start_points, end_points, normals = get_face_center(grouped_points['Aperture'])
            face_vector_polydata = create_arrows(start_points, end_points, normals)
            writer = vtk.vtkPolyDataWriter()
            writer.SetFileName('Aperture vectors.vtk')
            writer.SetInputConnection(face_vector_polydata.GetOutputPort())
            writer.Write()
            file_names.append('Aperture vectors')

        if grids:
            if grids[0]:
                base_geo_points = get_grid_base(grids[0])[0]
                # Create face normals
                start_points, end_points, normals = get_face_center(base_geo_points)
                face_vector_polydata = create_arrows(start_points, end_points, normals)
                writer = vtk.vtkPolyDataWriter()
                writer.SetFileName('grid base vectors.vtk')
                writer.SetInputConnection(face_vector_polydata.GetOutputPort())
                writer.Write()
                file_names.append('grid base vectors')


            if grids[1]:
                mesh_points = get_grid_mesh(grids[1])[0]
                # Create face normals
                start_points, end_points, normals = get_face_center(mesh_points)
                face_vector_polydata = create_arrows(start_points, end_points, normals)
                writer = vtk.vtkPolyDataWriter()
                writer.SetFileName('grid mesh vectors.vtk')
                writer.SetInputConnection(face_vector_polydata.GetOutputPort())
                writer.Write()
                file_names.append('grid mesh vectors')

        print(file_names)
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
