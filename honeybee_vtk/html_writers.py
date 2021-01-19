import os
import vtk
from .to_vtk import create_polygons
from .vtkjs_helper import convertDirectoryToZipFile, addDataToViewer



def write_json(
        grouped_points, file_name, target_folder):
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
    vtk_polydata_extended = create_polygons(grouped_points)
    writer = vtk.vtkJSONDataSetWriter()
    file_name = os.path.join(target_folder, file_name)
    writer.SetFileName(file_name)
    writer.SetInputConnection(vtk_polydata_extended.GetOutputPort())
    writer.Write()
    print(file_name)
    return file_name


def write_html(file_path, file_name, target_folder, include_grids, include_vectors,
               hbjson):
    print("Write HTML")
    return None
    # Get points and face_types from HBJSON
    points, hb_types = read_hbjson(hbjson)

    # Get points grouped for each Honeybee face_type
    grouped_points = group_by_face_type(points, hb_types)

    # Write VTK files based on Honeybee face_type and Honeybee object type
    for hb_type in grouped_points:
        write_json(grouped_points[hb_type], hb_type, target_folder)

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


