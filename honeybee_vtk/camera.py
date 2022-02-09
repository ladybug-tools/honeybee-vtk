"""A VTK camera object."""


import vtk
import math
from pathlib import Path
from typing import Tuple, List, Union, TypeVar, Type
from honeybee_radiance.view import View
from ladybug_geometry.geometry3d import Point3D, LineSegment3D


T = TypeVar('T', bound='Camera')


def _get_focal_point(focal_point: Union[Tuple[float, float, float], None],
                     position: Tuple[float, float, float],
                     direction: Tuple[float, float, float]) -> Tuple[float, float, float]:
    """Set the focal point of the camera.

    Args:
        focal_point: x, y, z coordinates of the focal point. If not set, the focal
            point will be set by moving the point of camera position in the direction
            of the camera direction.
        position: x, y, z coordinates of the camera position.
        direction: x, y, z components of the camera direction.

    Returns:
        x, y, z coordinates of the focal point.
    """
    if not focal_point:
        return (position[0] + direction[0], position[1] + direction[1], position[2] +
                direction[2])
    return focal_point


def _apply_projection(camera: Type[T], projection: str, parallel_scale: int,
                      clipping_range: Tuple[float, float]) -> vtk.vtkCamera:
    """Set the parallel projection camera.

    Args:
        camera: A VTK camera object.
        projection: The projection type. 'v' or 'l'
        parallel_scale: The parallel scale of the camera.
        clipping_range: The clipping range of the camera.

    Returns:
        A VTK camera object.
    """
    if projection == 'l':
        camera.ParallelProjectionOn()
        if parallel_scale:
            camera.SetParallelScale(parallel_scale)
        if clipping_range:
            camera.SetClippingRange(clipping_range)
        return camera
    return camera


class Camera(View):
    """Create a vtk camera object.

    This object inherits from the Honeybee_radiance.View object.
    https://www.ladybug.tools/honeybee-radiance/docs/honeybee_radiance.view.html

    Args:
        identifier: A unique name for the camera. Defaults to 'camera'.
        position: x, y, z coordinates of the camera in a 3D space. Defaults to (0, 0, 100)
            which puts the camera 100 meters off of the XY plane (ground).
        direction: x, y, and z components of a vector that represents the view direction
            (aim) of the camera. Defaults to (0, 0, -1). Which means the camera will look 
            towards the XY plane (ground).
        up_vector: x, y, and z component of the vector that represents where the top 
            of the camera is. Defaults to (0, 1, 0).
        view_angle: The angular hight of the camera view in degrees. You can think of 
            this as the vertical view angle. Defaults to 60
        projection: Choose between a perspective and parallel view type. 'v' will set
            the perspective view and 'l' will set the parallel view. Defaults to 'v'.
        reset_camera: A boolean that indicates whether the camera should be reset.
            Resetting the camera is helpful when you want to capture an image of a 
            model from outside the model. This will make sure that the camera is far 
            away from the model and the whole model is captured. This should be set
            to false in case of the intention is to take snapshots inside the model. 
            A use case is taking the snapshots of the grids in the model.
            Defaults to True.
        focal_point: x, y, and z coordinates of the point where the camera is looking at.
            Defaults to None which means the camera will look towards the XY plane 
            (ground).
        clipping_range: A range of two numbers that define the near plane and the far
            plane respectively. Both of these planes are perpendicular to the camera
            direction and are effective only in when the view type is parallel. The 
            distance from the camera to the near plane is the closest distance that
            an object can be to the camera and still remain in the view. The distance
            from the camera to the far plane is the farthest distance that an object
            can be from the camera and still remain in the view. Defaults to None.
        parallel_scale: Set the parallel scale for the camera. Note, that this parameters 
            works as an inverse scale. So larger numbers produce smaller images.This can
            be thought of as the zoom in and zoom out control. This parameter is effective
            only when the view type is parallel. Defaults to None.
        """

    def __init__(self, identifier: str = 'camera',
                 position: Tuple[float, float, float] = (0, 0, 100),
                 direction: Tuple[float, float, float] = (0, 0, -1),
                 up_vector: Tuple[float, float, float] = (0, 1, 0),
                 view_angle: int = 60,
                 projection: str = 'v',
                 reset_camera: bool = True,
                 focal_point: Union[Tuple[float, float, float], None] = None,
                 clipping_range: Union[Tuple[float, float], None] = None,
                 parallel_scale: Union[int, None] = None) -> None:

        super().__init__(
            identifier=identifier, position=position, direction=direction,
            up_vector=up_vector, h_size=view_angle, type=projection)

        self._view_angle = view_angle
        self._projection = projection
        self._reset_camera = reset_camera
        self._focal_point = focal_point
        self._clipping_range = clipping_range
        self._parallel_scale = parallel_scale

    @property
    def reset_camera(self) -> bool:
        """Get a boolean that indicates whether the camera should be reset."""
        return self._reset_camera

    @reset_camera.setter
    def reset_camera(self, reset_camera: bool) -> None:
        """Set a boolean that indicates whether the camera should be reset. This is
            helpful in case of the intention is to take snapshots inside the model.
        """
        self._reset_camera = reset_camera

    def to_vtk(self) -> vtk.vtkCamera:
        """Get a vtk camera object"""

        camera = vtk.vtkCamera()
        camera.SetPosition(self.position)
        camera.ComputeViewPlaneNormal()
        camera.SetViewUp(self.up_vector)

        camera.SetViewAngle(self._view_angle)
        camera.SetFocalPoint(_get_focal_point(self._focal_point, self.position,
                                              self.direction))
        camera = _apply_projection(camera, self._projection, self._parallel_scale,
                                   self._clipping_range)
        camera.OrthogonalizeViewUp()
        return camera

    @classmethod
    def from_view(cls: Type[T], view: View) -> T:
        """Create a Camera object from a radiance view.

        Args:
            view: A radiance view

        Returns:
            A Camera object.
        """
        return cls(identifier=view.identifier, position=view.position,
                   direction=view.direction, up_vector=view.up_vector,
                   view_angle=view.h_size if view.h_size > view.v_size else view.v_size,
                   projection=view.type)

    @classmethod
    def from_view_file(cls: Type[T], file_path: str) -> T:
        """Create a Camera object from a radiance view file.

        Args:
            file_path: A valid path to a radiance view file with .vf extension.

        Returns:
            A Camera object.
        """

        view_file = Path(file_path)

        if view_file.is_file() and view_file.as_posix()[-3:] == '.vf':
            return cls.from_view(view=View.from_file(view_file.as_posix()))
        else:
            raise FileNotFoundError(
                'Radiance view file not found.'
            )

    @classmethod
    def aerial_cameras(cls: Type[T], bounds: List[Point3D], centroid: Point3D) -> List[T]:
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

        # generate total four points at 45 degrees and -45 degrees on left and right
        # side of the centroid
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

        # default camera identifiers
        names = ['45_degrees', '315_degrees', '225_degrees', '135_degrees']

        # create cameras from four points. These cameras look at the centroid.
        default_cameras = []
        for i in range(len(camera_points)):
            point = camera_points[i]
            direction = directions[i]
            default_cameras.append(cls(identifier=names[i], position=(point.x, point.y, point.z),
                                       direction=(direction.x, direction.y, direction.z),
                                       up_vector=(0, 0, 1)))

        return default_cameras
