"""Function to create geometry to add to the Honeybee-vtk Model object."""

from ladybug_geometry.geometry3d import Face3D, Mesh3D, Vector3D, Point3D
from honeybee_radiance.sensorgrid import SensorGrid
from math import radians
from typing import List


def _radial_grid(sensorgrid: SensorGrid,
                 angle: float = 22.5) -> Mesh3D:
    """Create a radial grid from a SensorGrid.

    This function will create a triangle from each sensor in the grid.

    Args:
        sensorgrid: A SensorGrid object.
        angle: Angle between the two sides of a triangle in degrees.

    Returns:
        A Mesh3D object that a triangle as a mesh face for each sensor in the grid.
    """

    faces: List[Face3D] = []

    for sensor in sensorgrid.sensors:
        vec = Vector3D(*sensor.dir).normalize()
        vec_1 = vec.rotate_xy(angle=radians(angle*-1))
        vec_2 = vec.rotate_xy(angle=radians(angle))
        origin = Point3D(*sensor.pos)
        corner_1 = origin.move(vec_1)
        corner_2 = origin.move(vec_2)
        face = Face3D(boundary=[origin, corner_1, corner_2])
        faces.append(face)

    return Mesh3D.from_face_vertices(faces, False)
