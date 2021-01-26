"""Functions to extract geometry and metadata from a valid HBJSON."""

from .helper import get_mesh_points, check_convex
from .helper import get_point3d
from typing import List, Tuple, Dict


def get_rooms(rooms: List) -> Tuple[List[List], List[str]]:
    """Read rooms in HBJSON.

    Args:
        rooms: A list of Room objects from HBJSON.

    Returns:
        A tuple of two elements.

        - points: A list of lists of Point3Ds. Each list has three or more
            Point3Ds that can be used to create a Ladybug Face3D object.

        - hb_types: A list of text strings. Each text string represents either the
            Honeybee face type or the Honeybee face object for each list of Point3Ds
            in points.
    """
    points = []
    hb_types = []

    for room in rooms:
        for face in room['faces']:
            hb_types.append(face['face_type'])
            points.append(get_point3d(face['geometry']['boundary']))
            if 'apertures' in face:
                for aperture in face['apertures']:
                    hb_types.append(aperture['type'])
                    points.append(get_point3d(aperture['geometry']['boundary']))
                    if 'outdoor_shades' in aperture:
                        for outdoor_shade in aperture['outdoor_shades']:
                            hb_types.append(outdoor_shade['type'])
                            points.append(get_point3d(
                                outdoor_shade['geometry']['boundary']))

    return points, hb_types


def get_data(hbjson: Dict, hb_type: str) -> Tuple[List[List], List[str]]:
    """Get a list of vertices and Honeybee objects from an HBJSON object.

    Here, hb_type only accepts the values of 'face_type' and 'type'

    Args:
        hbjson_obj: An HBJSON object.
        hb_type: A string for Honeybee face_type or a Honeybee object.

    Returns:
        A tuple of two elements.

        - points: A list of lists of Point3Ds. Each list has three or more
            Point3Ds that can be used to create a Ladybug Face3D object.

        - hb_types: A list of text strings. Each text string represents either the
            Honeybee face type or the Honeybee face object for each list of Point3Ds
            in points.
    """
    points = []
    hb_types = []

    for key in hbjson:

        if 'holes' not in key['geometry']:
            if check_convex(key['geometry']['boundary']):
                points.append(get_point3d(key['geometry']['boundary']))
                hb_types.append(key[hb_type])
            else:
                triangles_points = get_mesh_points(key['geometry']['boundary'])
                for point3ds in triangles_points:
                    points.append(point3ds)
                    hb_types.append(key[hb_type])
        else:
            try:
                triangles_points = get_mesh_points(key['geometry']['boundary'],
                    key['geometry']['holes'])
            except ValueError:
                face_id = key['identifier']
                raise ValueError(
                    f'Face with id {face_id} could not be converted into triangulated'
                    ' mesh.'
                )
            else:
                for point3ds in triangles_points:
                    points.append(point3ds)
                    hb_types.append(key[hb_type])

    return points, hb_types


def read_hbjson(hbjson: Dict) -> Tuple[List[List], List[str]]:
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

    obj_type = {
        'faces': 'face_type',
        'orphaned_faces': 'face_type',
        'orphaned_shades': 'type',
        'orphaned_apertures': 'type',
        'orphaned_doors': 'type',
    }

    for key, value in obj_type.items():
        if key in hbjson:
            pts, types = get_data(hbjson[key], value)
            points.extend(pts)
            hb_types.extend(types)
    
    if 'rooms' in hbjson:
        pts, types = get_rooms(hbjson['rooms'])
        points.extend(pts)
        hb_types.extend(types)

    return points, hb_types


def group_by_face_type(points: List[List], hb_types: List[str]) -> dict:
    """Group points based on Honeybee type.

    Here, the text in hb_types will be one of the following;
    "Wall", "Floor", "RoofCeiling", "Airwall", "Aperture", "Shade", "Door"

    Args:
        points: A list of lists of Ladybug Point3D objects.
        hb_types: A list containing text strings for honeybee face_type and/or type

    Returns:
        A dictionary with Honeybee type as keys and list of lists of Point3Ds for
        geometry that belongs to that Honeybee type. An example would be;
        {
        'Wall': [[Point1, Point2, Point3], [Point4, Point5, Point6, Point7]],
        'Aperture': [[Point1, Point2, Point3], [Point4, Point5, Point6, Point7]]
        }
    """
    grouped_points = {face_type: [] for face_type in hb_types}

    for point, face_type in zip(points, hb_types):
        grouped_points[face_type].append(point)

    return grouped_points


def check_grid(hbjson: Dict) -> Tuple[List, List, List]:
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
            elif 'mesh' in grid:
                grid_with_mesh.append(grid)
            else:
                grid_with_points.append(grid)

        return grid_with_base, grid_with_mesh, grid_with_points


def get_grid_base(grids: List) -> Tuple[List[List], List[List]]:
    """Get vertices and normals for base geometry from Sensorgrid objects in HBJSON.

    Args:
        grids: A list of Sensorgrid objects in HBJSON.

    Returns:
        A tuple of two elements.

        - base_geometry_points: A list of lists of Point3Ds. Each list has three or more
            Point3Ds that can be used to create a Ladybug Face3D object.

        - vectors: A list of grid vectors where each vector is a list of X, Y, and Z
            component of a vector.
    """

    base_geometry_points = []
    vectors = []

    for grid in grids:
        for face in grid['base_geometry']:
            points = [point for point in face['boundary']]
            if check_convex(points):
                base_geometry_points.append(get_point3d(points))
            else:
                triangles_points = get_mesh_points(points)
                for point3ds in triangles_points:
                    base_geometry_points.append(point3ds)

        for sensors in grid['sensors']:
            vectors.append(sensors['dir'])

    return base_geometry_points, vectors


def get_grid_mesh(grids: List) -> Tuple[List[List], List[List]]:
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


def get_grid_points(grids: List) -> Tuple[List[List], List[List]]:
    """Get grid points and grid normals from Sensorgrid objects in HBJSON.

    Args:
        grids: A list of Sensorgrid objects in HBJSON.

    Returns:
        A tuple of three elements.

        - start_points: A list of points. Here, each points is a list of X, Y, and Z
            coordinates of the point.

        - vectors: A list of grid vectors where each vector is a list of X, Y, and Z
            component of a vector.
    """

    start_points = []
    vectors = []

    for grid in grids:
        for sensors in grid['sensors']:
            start_points.append(sensors['pos'])
            vectors.append(sensors['dir'])

    return start_points, vectors
