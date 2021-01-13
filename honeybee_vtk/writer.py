"""Write vtk files to the disk."""

import os
import json
import warnings

from zipfile import ZipFile
from honeybee.typing import clean_string
from .hbjson import read_hbjson
from .hbjson import check_grid, get_grid_base, get_grid_mesh, get_grid_points
from .tovtk import group_by_face_type
from .tovtk import write_polydata, write_color_grouped_points, write_arrows
from .helper import get_face_center


def write_vtk(
        file_path, *, file_name=None, get_grids=True,
        get_vectors=True):

    """Reads a valid HBJSON and writes a .zip of vtk files to the disk.

    Args:
        file_path: A text string for a valid path to the HBJSON file.
        file_name: A text string for the name of the .zip file to be written. If no
            text string is provided, the name of the HBJSON file will be used as a
            file name for the .zip file.
        get_grids: A boolean. Defaults to True. Grids will not be extracted from HBJSON
            if set to False.
        get_vectors: A boolean. Defaults to True. Vector arrows will not be created if
            set to False.
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

        # Write VTK files based on Honeybee face_type and Honeybee object type
        for hb_type in grouped_points:
            write_polydata(grouped_points[hb_type], hb_type)

        # Names of VTK files to be written
        file_names = list(grouped_points.keys())

        # write grid points to a vtk file if grids are found in HBJSON
        grids = check_grid(hbjson)

        # If grids are there in HBJSON and they are requested
        if grids and get_grids:

            # If base_geometry is found
            if grids[0]:
                base_geo_points = get_grid_base(grids[0])[0]
                write_polydata(base_geo_points, 'grid base')
                file_names.append('grid base')

            # If base_geometry is not found but mesh faces are found
            if grids[1]:
                mesh_points = get_grid_mesh(grids[1])[0]
                write_polydata(mesh_points, 'grid mesh')
                file_names.append('grid mesh')

            # If only grid points are found
            if grids[2]:
                start_points, end_points, vectors = get_grid_points(grids[2])
                write_color_grouped_points(start_points, vectors)
                file_names.append('grid points')
        else:
            pass
        
        # Write vectors if they are requested
        if get_vectors:
            
            # If Aperture objects are there in HBJSON
            if 'Aperture' in hb_types:
                # Create face normals
                start_points, end_points, normals = get_face_center(
                    grouped_points['Aperture'])
                write_arrows(start_points, end_points, normals, 'Aperture')
                file_names.append('Aperture vectors')
            
            # If grids are found in HBJSON
            if grids:
                
                # If base_geometry is found in any of the grids
                if grids[0]:
                    base_geo_points = get_grid_base(grids[0])[0]
                    start_points, end_points, normals = get_face_center(base_geo_points)
                    write_arrows(start_points, end_points, normals, 'grid base')
                    file_names.append('grid base vectors')

                # If mesh is found in any of the grids
                if grids[1]:
                    mesh_points = get_grid_mesh(grids[1])[0]
                    start_points, end_points, normals = get_face_center(mesh_points)
                    write_arrows(start_points, end_points, normals, 'grid mesh')
                    file_names.append('grid mesh vectors')
        else:
            pass
        
        # Use the name of HBJSON if file name is not provided
        if not file_name:
            name = '.'.join(os.path.basename(file_path).split('.')[:-1])
            file_name = clean_string(name)

        # Create a .zip file to capture all the generated .vtk files
        zipobj = ZipFile(file_name + '.zip', 'w')
        
        # Capture vtk files in a zip file.
        for file_name in file_names:
            zipobj.write(file_name + '.vtk')
        zipobj.close()

        # Delete vtk files if there is permission
        for file_name in file_names:
            try:
                os.remove(file_name + '.vtk')
            except OSError:
                warnings.warn(
                    'Honeybee does not have permission to delete files. You can delete' 
                    ' the .vtk files manually.'
                )
