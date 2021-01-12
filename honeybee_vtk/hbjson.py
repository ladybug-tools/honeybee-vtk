"""Extracts geometry and metadata from a valid Honeybee Json (HBJSON)"""
from .helper import get_mesh_points, check_convex
from .helper import face_center, get_point3d, get_end_point


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

    for obj in hbjson_obj:
        
        if 'holes' not in obj['geometry']:
            if check_convex(obj['geometry']['boundary']):
                points_lst.append(get_point3d(obj['geometry']['boundary']))
                hb_types.append(obj[hb_type])
            else:
                triangles_points = get_mesh_points(obj['geometry']['boundary'])
                for point_lst in triangles_points:
                    points_lst.append(point_lst)
                    hb_types.append(obj[hb_type])

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

    return points_lst, hb_types


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

    points_lst, hb_type_lst = get_data(hbjson['orphaned_faces'],
        'face_type')
    points.extend(points_lst)
    hb_types.extend(hb_type_lst)

    if 'orphaned_shades' in hbjson:
        points_lst, hb_type_lst = get_data(hbjson['orphaned_shades'],
            'type')
        points.extend(points_lst)
        hb_types.extend(hb_type_lst)

    if 'orphaned_apertures' in hbjson:
        points_lst, hb_type_lst = get_data(hbjson['orphaned_apertures'],
            'type')
        points.extend(points_lst)
        hb_types.extend(hb_type_lst)

    if 'orphaned_doors' in hbjson:
        points_lst, hb_type_lst = get_data(hbjson['orphaned_doors'],
            'type')
        points.extend(points_lst)
        hb_types.extend(hb_type_lst)

    return points, hb_types


def check_grid(hbjson):
    if 'sensor_grids' in hbjson['properties']['radiance']:
        grid_with_base = []
        grid_with_mesh = []
        grid_with_points = []
        for grid in hbjson['properties']['radiance']['sensor_grids']:
            if 'base_geometry' in grid:
                grid_with_base.append(grid)
            elif 'mesh' in grid and 'base_geometry' not in grid:
                grid_with_mesh.append(grid)
            else:
                grid_with_points.append(grid)
        return grid_with_base, grid_with_mesh, grid_with_points


def get_grid_base(grids):

    base_geo_points = []
    vectors = []

    for grid in grids:
        for face in grid['base_geometry']:
            points = [point for point in face['boundary']]
            base_geo_points.append(get_point3d(points))

        for sensors in grid['sensors']:
            vectors.append(sensors['dir'])

    return base_geo_points, vectors


def get_grid_mesh(grids):
    
    # Here, mesh_points is a list of lists.
    #[[[Mesh point 1], [Mesh point 2], [Mesh point 3], [Mesh point 4]]]
    mesh_points = []
    vectors = []

    for grid in grids:
        vertices = grid['mesh']['vertices']
        faces = grid['mesh']['faces']
        
        for face in faces:
            points = [vertices[face[i]] for i in range(len(face))]
            mesh_points.append(get_point3d(points))
            
        for sensors in grid['sensors']:
            vectors.append(sensors['dir'])

    return mesh_points, vectors


def get_grid_points(grids):
    """Get grid points and grid normals from a Sensorgrid object in HBJSON.

    Args:
        grids: A list of Sensorgrid objects in HBJSON.

    Returns:
        A tuple of two elements.

        - start_points: A list of lists of vertices(X, Y, Z) for each grid point.

        - end_normals: A list of lists of normals(X, Y, Z) for each grid point moved in
            the direction of the vector.

        - vectors: A list of grid vectors where each vector is a list of X, Y, and Z
            component of a vector.
    """

    start_points = []
    vectors = []
    end_points = []

    for grid in grids:
        for sensors in grid['sensors']:
            start_points.append(sensors['pos'])
            vectors.append(sensors['dir'])
    
    for i in range(len(start_points)):
        end_point = get_end_point(start_points[i], vectors[i])
        end_points.append(end_point)

    return start_points, end_points, vectors







