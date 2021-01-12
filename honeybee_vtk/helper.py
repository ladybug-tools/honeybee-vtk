"""Functions to help in geometry translation."""

from ladybug_geometry.geometry3d import Face3D, Point3D


def get_mesh_points(boundary_points, holes_points=None):
    """Convert a Face3D with holes in triangulated mesh and get vertices.

    This function constructs a Ladybug Face3D object from vertices and creates
    triangulated meshes from the generated Face3D object. The function then returns
    the vertices of these generated meshes.

    Args:
        boundary_points: A list of points that represent the boundary of a face. Here,
            each point is a list of X, Y, and Z cordinates of the point.
        holes_points: A list of lists of points that represent the boundary of the holes
            in the face. Here, each point is a list of X, Y, and Z cordinates of the
            point. Defaults to None. Which will mean the face has no holes.

    Returns:
        A list of list of points. Each list has vertices for a triangular polygon.
        Example of structure will be [[X, Y, Z], [X, Y, Z], [X, Y, Z]].
    """
    # Create Ladybug Point3D objects from boundary points
    lb_boundary_pts = [
        Point3D(point[0], point[1], point[2])
        for point in boundary_points]

    # Create a Ladybug Face3D object from boundary points and hole points
    if holes_points:
        # Create Ladybug Point3D objects from hole points
        lb_holes_pts = [
            [Point3D(point[0], point[1], point[2]) for point in points]
            for points in holes_points]

        face = Face3D(boundary=lb_boundary_pts, holes=lb_holes_pts)

    else:
        face = Face3D(boundary=lb_boundary_pts)

    # Generate triangles from the Face3D object
    triangles = face.triangulated_mesh3d

    # A list of lists with each list having vertices of triangles
    points_lst = [[
        triangles.vertices[face[0]], triangles.vertices[face[1]],
        triangles.vertices[face[2]]] for face in triangles.faces]

    return points_lst


def check_convex(boundary_points):
    """Check whether a Face3D is convex or not.

    This function creates a Ladybug Face3D object from boundary points and reports
    whether the Face3D is convex or not.

    Args:
        boundary_points: A list of list of points. Here, each point is a list of 
            X, Y, and Z cordinates of the point.

    Returns:
        A boolean value.
    """

    lb_boundary_pts = [
        Point3D(point[0], point[1], point[2]) for point in boundary_points]

    face = Face3D(boundary=lb_boundary_pts)

    return face.is_convex


def get_point3d(points):
    """Convert a list of points in to a list of Ladybug Point3D objects.

    Args:
        points: A list of points. Here, each point is a list of 
            X, Y, and Z cordinates of the point.

    Returns:
        A list of Ladybug Point3D objects.
    """
    return [Point3D(point[0], point[1], point[2]) for point in points]


def get_end_point(point, vector):
    """Move a point in the direction of a vector and return the moved point.

    Here, each point is a list of 
            X, Y, and Z cordinates of the point.

    Args:
        point: A point as a list where the list has X, Y, and Z cordinates of the point.
        vector: A vector as a list where the list has X, Y, and Z component of the
            vectors.

    Returns:
        A point as a list where the list has X, Y, and Z cordinates of the point.
    """
    return [point[0] + vector[0], point[1] + vector[1], point[2] + vector[2]]


def face_center(points):
    """Get center point and normal for a Ladybug Face3D.

    This function creates a Ladybug Face3D from the points and returns its center and
    normal properties.

    Args:
        points: A list of Ladybug Point3D objects that can be a boundary for a face.

    Returns:
        A tuple with two elements

        - face.center: The center point of the face as a Ladybug Point3D object.

        - face.normal: The face normal for the Ladybug Face3D.
    """
    face = Face3D(boundary=points)
    return face.center, face.normal


def get_face_center(points_lst):
    """Get geometry to create an arrow at the center of the face.

    Args:
        points_lst: A list of lists. Where each list has X,Y, and Z cordinates of a
            point.

    Returns:
        A tuple with three elements

        - start_points: A list Ladybug Point3D objects. These are start points for
            each Face3D created from points provided to the function.
        
        - end_points: A list of Ladybug Point3D objects. These points are derived by
            moving the center point of a Face3D using the vector of the Face3D.
        
        - normals: A list of Ladybug Vector3D objects.
    """
    start_points = [face_center(points)[0] for points in points_lst]
    normals = [face_center(points)[1] for points in points_lst]
    end_points = [
        get_end_point(start_points[i], normals[i]) for i in range(len(start_points))]

    return start_points, end_points, normals
