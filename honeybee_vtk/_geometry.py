"""Function to create geometry to add to the Honeybee-vtk Model object."""

from ladybug_geometry.geometry3d import Face3D, Mesh3D, Vector3D, Point3D
from honeybee_radiance.sensorgrid import SensorGrid
from math import radians
from typing import List


def _radial_grid(sensorgrid: SensorGrid,
                 angle: float = 45,
                 radius: float = None) -> Mesh3D:
    """Create a radial grid from a SensorGrid.

    This function will create a triangle from each sensor in the grid using the
    sensors' positions and direction.

    Args:
        sensorgrid: A SensorGrid object.
        angle: Angle between the two sides of a triangle in degrees. If not
            provided, the default value will be 45 degrees.
        radius: Height of the triangle in meters. If None, the height of the 
            triangle will be decided based on the magnitude of the sensor's direction 
            vector.

    Returns:
        A Mesh3D object that has a triangle as a mesh face for each sensor in the grid.
    """

    faces: List[Face3D] = []

    for sensor in sensorgrid.sensors:
        vec = Vector3D(*sensor.dir).normalize()
        vec_1 = vec.rotate_xy(angle=radians((angle/2)*-1))
        vec_2 = vec.rotate_xy(angle=radians(angle/2))
        origin = Point3D(*sensor.pos)
        if radius is None:
            corner_1 = origin.move(vec_1)
            corner_2 = origin.move(vec_2)
        else:
            corner_1 = origin.move(vec_1*radius)
            corner_2 = origin.move(vec_2*radius)
        face = Face3D(boundary=[origin, corner_1, corner_2])
        faces.append(face)

    return Mesh3D.from_face_vertices(faces, False)
