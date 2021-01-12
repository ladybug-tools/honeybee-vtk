"""Functions to extract geometry and metadata from a valid HBJSON."""

from .helper import get_mesh_points, check_convex
from .helper import get_point3d, get_end_point


def get_data(hbjson_obj, hb_type):
    """Get a list of vertices and Honeybee objects from an HBJSON object.

    Here, hb_type only accepts the values of 'face_type' and 'type'

    Args:
        hbjson_obj: An HBJSON object.
        hb_type: A string for Honeybee face_type or a Honeybee object.

    Returns:
        A tuple of two elements.

        - points_lst: A list of lists of Point3Ds. Each list has three or more 
            Point3Ds that can be used to create a Ladybug Face3D object.

        - hb_types: A list of text strings. Each text string represents either the 
            Honeybee face type or the Honeybee face object for each list of Point3Ds
            in points.
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
        
        - points: A list of lists of Point3Ds. Each list has three or more 
            Point3Ds that can be used to create a Ladybug Face3D object.

        - hb_types: A list of text strings. Each text string represents either the 
            Honeybee face type or the Honeybee face object for each list of Point3Ds
            in points.
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
    """Check whether the HBJSON has grid objects.

    Args:
        hbjson: A valid HBJSON (Honeybee JSON).

    Returns:
        A tuple of three elements.

        - grid_with_base: A list of Sensorgrid objects for Sensorgrids that have
            "base_geometry" as a key
        
        - grid_with_mesh: A list of Sensorgrid objects for Sensorgrids that have
            "mesh" as a key and don't have "base_geometry" as a key.
        
        - grid_with_points: A list of Sensorgrid objects for Sensorgrids that don't have
            "mesh" and "base_geometry" keys.
    """
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
    """Get vertices and normals for base geometry from Sensorgrid objects in HBJSON.

    Args:
        grids: A list of Sensorgrid objects in HBJSON.

    Returns:
        A tuple of two elements.

        - base_geo_points: A list of lists of Point3Ds. Each list has three or more 
            Point3Ds that can be used to create a Ladybug Face3D object.

        - vectors: A list of grid vectors where each vector is a list of X, Y, and Z
            component of a vector.
    """

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
    """Get mesh vertices and grid normals from Sensorgrid objects in HBJSON.

    Args:
        grids: A list of Sensorgrid objects in HBJSON.

    Returns:
        A tuple of two elements.

        - mesh_points: A list of lists of Point3Ds. Each list has three or more Point3Ds
            that can be used to create a Ladybug Face3D object.
        
        - vectors: A list of grid vectors where each vector is a list of X, Y, and Z
            component of a vector.
    """
    
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
    """Get grid points and grid normals from Sensorgrid objects in HBJSON.

    Args:
        grids: A list of Sensorgrid objects in HBJSON.

    Returns:
        A tuple of three elements.

        - start_points: A list of points. Here, each points is a list of X, Y, and Z
            cordinates of the point.

        - end_points: A list of lists. End point is derived by moving the start
            point using a vector. Here, each point is a list of X, Y, and Z 
            cordinates of the point.

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
        end_points.append(get_end_point(start_points[i], vectors[i]))

    return start_points, end_points, vectors
