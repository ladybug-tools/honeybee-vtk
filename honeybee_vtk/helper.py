"""Functions to help in geometry translation."""

from ladybug_geometry.geometry3d import Face3D, Point3D, Vector3D
from typing import List, Tuple


def get_mesh_points(
        boundary_points: List[List],
        holes_points: List[List] = None) -> List[List]:

    """Convert a Face3D with holes in triangulated mesh and get vertices.

    This function constructs a Ladybug Face3D object from vertices and creates
    triangulated meshes from the generated Face3D object. The function then returns
    the vertices of these generated meshes.

    Args:
        boundary_points: A list of points that represent the boundary of a face. Here,
            each point is a list of X, Y, and Z coordinates of the point.
        holes_points: A list of lists of points that represent the boundary of the holes
            in the face. Here, each point is a list of X, Y, and Z coordinates of the
            point. Defaults to None. Which will mean the face has no holes.

    Returns:
        A list of lists. Each list has three Point3D objects that represent the vertices
        of triangles.
    """
    # Create Ladybug Point3D objects from boundary points
    lb_boundary_pts = [Point3D(*point) for point in boundary_points]

    # Create a Ladybug Face3D object from boundary points and hole points
    if holes_points:
        # Create Ladybug Point3D objects from hole points
        lb_holes_pts = [[Point3D(*point) for point in points] for points in holes_points]
        face = Face3D(boundary=lb_boundary_pts, holes=lb_holes_pts)
    else:
        face = Face3D(boundary=lb_boundary_pts)

    # Generate triangles from the Face3D object
    triangles = face.triangulated_mesh3d

    # A list of lists with each list having vertices of triangles
    points = [
        [triangles.vertices[face[0]],
            triangles.vertices[face[1]],
            triangles.vertices[face[2]]] for face in triangles.faces]

    return points


def check_convex(points: List[List]) -> bool:
    """Check whether a Face3D is convex or not.

    This function creates a Ladybug Face3D object from boundary points and reports
    whether the Face3D is convex or not.

    Args:
        points: A list of list of points that form the boundary of a face.
            Here, each point is a list of X, Y, and Z coordinates of the point.

    Returns:
        A boolean value.
    """

    lb_pts = [Point3D(*point) for point in points]
    face = Face3D(boundary=lb_pts)

    return face.is_convex


def triangulate_concave(hb_obj, hb_type):
    """If a Face3D is concave, this function will triangulate it.

    Args:
        hb_obj (HBJSON): An HBJSON object.
        hb_type (str): A text string representing Honeybee type. Either 'face_type' 
            or 'type'

    Returns:
        A tuple of two elements.

        -   points: A list of lists of Point3Ds. Each list has three or more
            Point3Ds that can be used to create a Ladybug Face3D object.

        -   hb_types: A list of text strings. Each text string represents either the
            Honeybee face type or the Honeybee face object for each list of Point3Ds
            in points.
    """
    points = []
    hb_types = []

    if check_convex(hb_obj['geometry']['boundary']):
                points.append(get_point3d(hb_obj['geometry']['boundary']))
                hb_types.append(hb_obj[hb_type])
    else:
        triangles_points = get_mesh_points(hb_obj['geometry']['boundary'])
        for point3ds in triangles_points:
            points.append(point3ds)
            hb_types.append(hb_obj[hb_type])
    
    return points, hb_types


def get_point3d(points: List[List]) -> List:
    """Convert a list of points in to a list of Ladybug Point3D objects.

    Args:
        points: A list of points. Here, each point is a list of
            X, Y, and Z coordinates of the point.

    Returns:
        A list of Ladybug Point3D objects.
    """
    return [Point3D(*point) for point in points]


def get_vector3d(points: List[List]) -> List:
    """Convert a list of vector component in to a list of Ladybug Vector3D objects.

    Args:
        points: A list of points. Here, each point is a list of
            X, Y, and Z components of a vector.

    Returns:
        A list of Ladybug Vector3D objects.
    """
    return [Vector3D(*point) for point in points]


def get_end_point(point, vector):
    """Move a point in the direction of a vector and return the moved point.

    Here, each point is a list of X, Y, and Z coordinates of the point.

    Args:
        point: A Ladybug Point3D object.
        vector: A Ladybug Vector3D object.

    Returns:
        A Ladybug Point3D object.
    """
    return Point3D(point.x + vector.x, point.y + vector.y, point.z + vector.z)


def get_vector_at_center(points: List[List[List]]) -> Tuple[List, List]:
    """Get geometry to create an arrow at the center of the face.

    Args:
        points: A list of lists. Where each list has X,Y, and Z coordinates of a
            point.

    Returns:
        A tuple with three elements.

        -   start_points: A list Ladybug Point3D objects. These are start points for each
        Face3D created from points provided to the function.

        -   vectors: A list of Ladybug Vector3D objects.
    """
    faces = [Face3D(boundary=pts) for pts in points]
    start_points = [face.center for face in faces]
    vectors = [face.normal for face in faces]

    return start_points, vectors
