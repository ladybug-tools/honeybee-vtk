"""Extracts geometry and metadata from a valid Honeybee Json (HBJSON)"""
from .helper import get_mesh_points, check_convex, joined_face_vertices_from_mesh
from .helper import face_center, get_point3d


def get_data(hbjson_obj, hb_type):
    """Get a list of vertices and Honeybee objects from an HBJSON object.

    Here, hb_type only accepts the values of 'face_type' and 'type'

    Args:
        obj: An HBJSON object
        hb_type: A string for Honeybee face_type or a Honeybee type

    Returns:
        A tuple of two elements.

        - points_lst: A list of lists of points for the geometry in the HBJSON

        - hb_types: A list of honeybee face_types and/or types for the geometry objects
            in the HBJSON.

    """
    points_lst = []
    hb_types = []
    display_name = []

    for obj in hbjson_obj:
        

        if 'holes' not in obj['geometry']:
            if check_convex(obj['geometry']['boundary']):
                points_lst.append(get_point3d(obj['geometry']['boundary']))
                hb_types.append(obj[hb_type])
                display_name.append(obj['display_name'])
            else:
                triangles_points = get_mesh_points(obj['geometry']['boundary'])
                for point_lst in triangles_points:
                    points_lst.append(point_lst)
                    hb_types.append(obj[hb_type])
                    display_name.append(obj['display_name'])

        else:
            try:
                triangles_points = get_mesh_points(obj['geometry']['boundary'],
                    obj['geometry']['holes'])
            except ValueError:
                face_id = obj['identifier']
                raise ValueError(
                    f'Face with id {face_id} could not be converted into triangulated'
                    ' mesh.'
                )
            else:
                for point_lst in triangles_points:
                    points_lst.append(point_lst)
                    hb_types.append(obj[hb_type])
                    display_name.append(obj['display_name'])

    return points_lst, hb_types, display_name


def get_grid(hbjson):
    """Get grid points and grid normals from HBJSON.

    Args:
        hbjson: A valid HBJSON (Honeybee JSON).

    Returns:
        A tuple of two elements.

        - start_points: A list of lists of vertices(X, Y, Z) for each grid point.

        - end_normals: A list of lists of normals(X, Y, Z) for each grid point moved in
            the direction of the vector.

        - vectors: A list of grid vectors.
    """

    start_points = []
    vectors = []
    end_points = []

    if 'sensor_grids' in hbjson['properties']['radiance']:
        for grid in hbjson['properties']['radiance']['sensor_grids']:
            for sensors in grid['sensors']:
                start_points.append(sensors['pos'])
                vectors.append(sensors['dir'])
        
        for i in range(len(start_points)):
            end_point = get_end_point(start_points[i], vectors[i])
            end_points.append(end_point)

        return start_points, end_points, vectors


def get_end_point(point, vector):
    """Move a point in the direction of a vector and return the moved point as a list."""

    return [point[0]+vector[0], point[1]+vector[1], point[2]+vector[2]]


def read_hbjson(hbjson):
    """Read and extract information from a valid HBJSON.

    Args:
        hbjson: A valid HBJSON (Honeybee JSON).

    Returns:
        A tuple with two elements. 
        
        - points: Points for the geometry in the HBJSON

        - hb_types: Honeybee face_types and/or types for the geometry objects
            in the HBJSON.
    """
    points = []
    hb_types = []
    display_names = []

    points_lst, hb_type_lst, display_names_lst = get_data(hbjson['orphaned_faces'],
        'face_type')
    points.extend(points_lst)
    hb_types.extend(hb_type_lst)
    display_names.extend(display_names_lst)
    
    if 'orphaned_shades' in hbjson:
        points_lst, hb_type_lst, display_names_lst = get_data(hbjson['orphaned_shades'],
            'type')
        points.extend(points_lst)
        hb_types.extend(hb_type_lst)
        display_names.extend(display_names_lst)
    
    if 'orphaned_apertures' in hbjson:
        points_lst, hb_type_lst, display_names_lst = get_data(hbjson['orphaned_apertures'],
            'type')
        points.extend(points_lst)
        hb_types.extend(hb_type_lst)
        display_names.extend(display_names_lst)
    
    if 'orphaned_doors' in hbjson:
        points_lst, hb_type_lst, display_names_lst = get_data(hbjson['orphaned_doors'],
            'type')
        points.extend(points_lst)
        hb_types.extend(hb_type_lst)
        display_names.extend(display_names_lst)

    return points, hb_types, display_names
    

def get_grid_mesh(hbjson):

    # Here, mesh_points is a list of lists.
    #[[[Mesh point 1], [Mesh point 2], [Mesh point 3], [Mesh point 4]]]
    mesh_points = []
    vectors = []
    mesh_faces = []

    if 'sensor_grids' in hbjson['properties']['radiance']:
        for grid in hbjson['properties']['radiance']['sensor_grids']:
            vertices = grid['mesh']['vertices']
            faces = grid['mesh']['faces']
            
            for face in faces:
                mesh_faces.append(face)
                points = [vertices[face[i]] for i in range(len(face))]
                mesh_points.append(points)

            for sensors in grid['sensors']:
                vectors.append(sensors['dir'])
    else:
        return None
    
    return mesh_points, mesh_faces, vectors


def get_joined_face_vertices(hbjson):
    vertices_lst = []
    if 'sensor_grids' in hbjson['properties']['radiance']:
        for grid in hbjson['properties']['radiance']['sensor_grids']:
            vertices = grid['mesh']['vertices']
            faces = grid['mesh']['faces']

            vertices_lst.extend(joined_face_vertices_from_mesh(vertices, faces))
    
    return vertices_lst


def get_mesh(hbjson):
    mesh_points = []
    mesh_faces = []

    if 'sensor_grids' in hbjson['properties']['radiance']:
        for grid in hbjson['properties']['radiance']['sensor_grids']:
            vertices = grid['mesh']['vertices']
            faces = grid['mesh']['faces']
            mesh_points.append(vertices)
            mesh_faces.append(faces)
    
        return mesh_points, mesh_faces
    

def get_face_center(points_lst):
    start_points = [face_center(points)[0] for points in points_lst]
    normals = [face_center(points)[1] for points in points_lst]
    end_points = [get_end_point(start_points[i], normals[i]) for i in range(len(start_points))]

    return start_points, end_points, normals



