"""A VTK camera object."""
from __future__ import annotations
import vtk
import math
from pathlib import Path
from typing import Tuple, List
from honeybee_radiance.view import View
from ladybug_geometry.geometry3d import Point3D, LineSegment3D


class Camera(View):
    """Create a vtk camera object.

        Args:
            identifier: A text string to be used as a name for the camera.
                Defaults to 'camera'.
            position: A tuple of three numbers that represent the x, y and z
                coordinates of camera in a 3D space. Defaults to (0, 0, 50). Which
                puts the camera 50 units off of ground (XY plane).
            direction: A tuple of three numbers that represent the x, y, and z
                components of a vector towards the aim of the camera.
                Defaults to (0, 0, -1). Which means the camera will look towards the
                ground (XY plane).
            up_vector: A tuple of three numbers to represent the x, y, and z
                component of the vector that represents where the top of the camera is.
                Defaults to (0, 1, 0).
            h_size: A number representing the horizontal view angle.
                Defaults to 60.
            v_size: A number representing the vertical view angle.
                Defaults to 60.
            type: Choose between a perspective and parallel view type. 'v' will set
                the perspective view and 'l' will set the parallel view. Defaults to 'v'
                which is the perspective view.
        """

    def __init__(
            self,
            identifier: str = 'camera',
            position: Tuple[float, float, float] = (0, 0, 100),
            direction: Tuple[float, float, float] = (0, 0, -1),
            up_vector: Tuple[float, float, float] = (0, 1, 0),
            h_size: int = 60,
            v_size: int = 30,
            type: str = 'v') -> None:

        super().__init__(
            identifier=identifier, position=position, direction=direction,
            up_vector=up_vector, h_size=h_size, v_size=v_size, type=type)

    def to_vtk(self) -> vtk.vtkCamera:
        """Get a vtk camera object."""
        camera = vtk.vtkCamera()

        # Parallel projection
        if self._type.value == 'l':
            camera.SetParallelProjection(True)
            camera.ParallelProjectionOn()
        # Perspective projection
        else:
            # The location of camera in a 3D space
            camera.SetPosition(self._position.value)

        # get a focal_point on the same axis as the camera position.
        fp = (self._position[0] + self._direction.value[0],
              self._position[1] + self._direction.value[1],
              self._position[2] + self._direction.value[2])
        # The direction to the point where the camera is looking at
        camera.SetFocalPoint(fp)

        # Where the top of the camera is
        camera.SetViewUp(self._up_vector.value)
        # Horizontal view angle
        camera.SetViewAngle(self._h_size.value)
        camera.SetUseHorizontalViewAngle(True)
        camera.UseHorizontalViewAngleOn()

        return camera

    @classmethod
    def from_view(cls: Camera, view: View) -> Camera:
        """Create a Camera object from a radiance view.

        Args:
            view: A radiance view

        Returns:
            A Camera object.
        """
        return cls(
            position=view.position,
            direction=view.direction,
            up_vector=view.up_vector,
            h_size=view.h_size,
            v_size=view.v_size,
            type=view.type)

    @classmethod
    def from_view_file(cls: Camera, file_path: str) -> Camera:
        """Create a Camera object from a radiance view file.

        Args:
            file_path: A valid path to a radiance view file with .vf extension.

        Returns:
            A Camera object.
        """

        view_file = Path(file_path)

        if view_file.is_file() and view_file.as_posix()[-3:] == '.vf':
            return Camera.from_view(view=View.from_file(view_file.as_posix()))
        else:
            raise FileNotFoundError(
                'Radiance view file not found.'
            )

    @classmethod
    def aerial_cameras(cls: Camera, bounds: List[Point3D], centroid) -> List[Camera]:
        """Get four aerial cameras.

        Args:
            bounds: A list of Point3D objects representing bounds of the actors in the
                scene.
            centroid: A Point3D object representing the centroid of the actors.

        Returns:
            A list of Camera objects.
        """

        # find the top most z-cordinate in the model
        cord_point = {point.z: point for point in bounds}
        topmost_z_cord = cord_point[sorted(cord_point, reverse=True)[0]].z

        # move centroid to the level of top most z-cordinate
        centroid_moved = Point3D(centroid.x, centroid.y,
                                 topmost_z_cord)

        # distance of four cameras from centroid
        distances = [centroid.distance_to_point(pt) for pt in bounds]
        farthest_distance = sorted(distances, reverse=True)
        camera_distance = farthest_distance[0]

        # generate four points at 45 degrees and -45 degrees on left and right side of
        # the centroid
        pt0 = Point3D(
            centroid_moved.x + math.cos(math.radians(45))*camera_distance,
            centroid_moved.y + math.sin(math.radians(45))*camera_distance,
            centroid_moved.z)
        pt1 = Point3D(
            centroid_moved.x + math.cos(math.radians(-45))*camera_distance,
            centroid_moved.y + math.sin(math.radians(-45))*camera_distance,
            centroid_moved.z)
        pt2 = Point3D(
            centroid_moved.x + math.cos(math.radians(45))*camera_distance*-1,
            centroid_moved.y + math.sin(math.radians(45))*camera_distance*-1,
            centroid_moved.z)
        pt3 = Point3D(
            centroid_moved.x + math.cos(math.radians(-45))*camera_distance*-1,
            centroid_moved.y + math.sin(math.radians(-45))*camera_distance*-1,
            centroid_moved.z)
        camera_points = [pt0, pt3, pt2, pt1]

        # get directions (vectors) from each point to the centroid
        directions = [LineSegment3D.from_end_points(
            pt, centroid).v for pt in camera_points]

        # create cameras from four points. These cameras must look at the centroid.
        default_cameras = []
        for i in range(len(camera_points)):
            point = camera_points[i]
            direction = directions[i]
            default_cameras.append(cls(position=(point.x, point.y, point.z),
                                       direction=(direction.x, direction.y, direction.z),
                                       up_vector=(0, 0, 1)))

        return default_cameras
