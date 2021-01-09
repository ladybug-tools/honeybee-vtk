"""Helper geometry translator functions."""

from ladybug_geometry.geometry3d import Face3D, Point3D, Mesh3D, Polyface3D, Polyline3D


def get_mesh_points(boundary_points, holes_points=None):
    """Convert a Face3D with holes in triangulated mesh and get vertices.

    This function constructs a Ladybug Face3D object from vertices and creates
    triangulated meshes from the generated Face3D object. The function then returns
    the vertices of these generated meshes.

    Args:
        boundary_points: A list of points that represent the boundary of a face. Here, 
            each point is a list of X, Y, and Z cordinate.
        holes_points: A list of lists of points that represent the boundary of the holes
            in the face. Here, each point is a list of X, Y, and Z cordinate.

    Returns:
        A list of list of points. Each list has vertices for a triangular polygon.
    """
    # Create Ladybug Point3D objects from boundary points
    lb_boundary_pts = [Point3D(point[0], point[1], point[2])
        for point in boundary_points]

    # Create a Ladybug Face3D object from boundary points and hole points
    if holes_points:
        # Create Ladybug Point3D objects from hole points
        lb_holes_pts = [[Point3D(point[0], point[1], point[2]) for point in point_lst]
            for point_lst in holes_points]

        face = Face3D(boundary=lb_boundary_pts, holes=lb_holes_pts)
    else:
        face = Face3D(boundary=lb_boundary_pts)
    
    # Generate triangles from the Face3D object
    triangles = face.triangulated_mesh3d

    # A list of lists with each list having vertices of triangles
    points_lst = [[triangles.vertices[face[0]], triangles.vertices[face[1]],
        triangles.vertices[face[2]]] for face in triangles.faces]
    
    return points_lst


def check_convex(boundary_points):

    lb_boundary_pts = [Point3D(point[0], point[1], point[2])
        for point in boundary_points]
    
    face = Face3D(boundary=lb_boundary_pts)

    if face.is_convex:
        return True


def joined_face_vertices_from_mesh(mesh_points, mesh_faces):
    
    vertices_lst = []
    for face in mesh_faces:
        points = []
        for i in range(len(face)):
            point = mesh_points[face[i]]
            point3d = Point3D(point[0], point[1], point[2])
            points.append(point3d)
        vertices_lst.append(points)
    
    face3ds = []
    for vert_lst in vertices_lst:
        face = Face3D(boundary=vert_lst)
        face3ds.append(face)
    
    face_normal_dict = {face: face.normal for face in face3ds}

    faces_grouped_by_vector = {}
    for i, v in face_normal_dict.items():
        faces_grouped_by_vector[v] = [i] if v not in faces_grouped_by_vector.keys() else faces_grouped_by_vector[v] + [i]

    faces_vertices_lst = []
    for vector in faces_grouped_by_vector:
        polyface = Polyface3D.from_faces(faces_grouped_by_vector[vector], 0.01)
        lines = list(polyface.naked_edges)
        polylines = Polyline3D.join_segments(lines, 0.01)
        face3d = Face3D(boundary=polylines[0].vertices)
        verts = [[vert.x, vert.y, vert.z] for vert in face3d.vertices]
        faces_vertices_lst.append(verts)

    return faces_vertices_lst


def get_point3d(point_lst):
    return [Point3D(point[0], point[1], point[2]) for point in point_lst]


def face_center(points):
    face = Face3D(boundary=points)
    return face.center, face.normal
    