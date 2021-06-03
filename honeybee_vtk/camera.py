"""A VTK camera object."""
from __future__ import annotations
import vtk
from pathlib import Path
from typing import List, Tuple
from ladybug_geometry.geometry3d.pointvector import Point3D
from honeybee_radiance.view import View


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

        self._flat_view_directions = {
            (0, 0, -1): [2, '+'],
            (0, 0, 1): [2, '-'],
            (0, 1, 0): [1, '+'],
            (0, -1, 0): [1, '-'],
            (1, 0, 0): [0, '+'],
            (-1, 0, 0): [0, '-'],
        }

    @property
    def flat_view_direction(self) -> dict:
        """This dictionary with, direction of camera : [index, +/-] structure.

        Here, index referers to the index of the camera position. For example, in case
        of (0, 0, -1), the camera will move along the Z axis. This means the z cordinate
        of camera position (index = 2) will be modified to move camera through space.
        The + and - indicates the direction on a particular axis. For example, [2, '+']
        means the camera will move along Z axis and in +Z direction.
        """
        return self._flat_view_directions

    def to_vtk(self, bounds: List[Point3D] = None) -> vtk.vtkCamera:
        """Get a vtk camera object."""
        camera = vtk.vtkCamera()

        # Parallel projection
        if self._type.value == 'l':

            # If a flat view in Parallel projection is requested
            if self._direction.value in self._flat_view_directions:
                if not bounds:
                    raise ValueError(
                        'Bounds of actors are required to generate one of the flat'
                        ' views. Use get_bounds method of the Actors object to get'
                        ' these bounds.'
                    )
                # get adjusted camera position
                position = self._adjusted_position(bounds)

            # If only parallel projection is requested
            else:
                # use the same camera postion
                position = self._position.value

            # The location of camera in a 3D space
            camera.SetPosition(position)
            # get a focal_point on the same axis as the camera position. This is
            # necessary for flat views
            fp = (position[0] + self._direction.value[0],
                  position[1] + self._direction.value[1],
                  position[2] + self._direction.value[2])

            # The direction to the point where the camera is looking at
            camera.SetFocalPoint(fp)
            camera.SetParallelProjection(True)
            # TODO: Need to find a better way to set parallel scale
            camera.SetParallelScale(self._v_size.value)
            camera.ParallelProjectionOn()

        # Perspective projection
        else:
            # The location of camera in a 3D space
            camera.SetPosition(self._position.value)
            # The direction to the point where the camera is looking at
            camera.SetFocalPoint(self._direction.value)

        # Where the top of the camera is
        camera.SetViewUp(self._up_vector.value)
        # Horizontal view angle
        camera.SetViewAngle(self._h_size.value)
        camera.SetUseHorizontalViewAngle(True)
        camera.UseHorizontalViewAngleOn()

        return camera

    def _adjusted_position(self, bounds: List[Point3D]) -> Tuple[float, float, float]:
        """Get adjusted camera position.

        This method helps bring camera close to the model within an offset distance.

        Returns:
            Adjusted camera position in the form of a tuple with three decimal values.
        """
        index = self._flat_view_directions[self._direction.value][0]
        nearest_point = self._outermost_point(bounds)
        cord = nearest_point[index]
        min_camera_offset = 1

        # If the cordinate we're looking for is negative the offset needs to be applied
        # in negative as well
        if cord <= 0:
            offset = min_camera_offset * -1
        else:
            offset = min_camera_offset

        # if the camera needs to move along x-axis
        if index == 0:
            adjusted_position = (cord + offset, self._position.value[1],
                                 self._position.value[2])

        # if the camera needs to move along y-axis
        elif index == 1:
            adjusted_position = (self._position.value[0], cord + offset,
                                 self._position.value[2])

        # if the camera needs to move along z-axis
        elif index == 2:
            adjusted_position = (self._position.value[0], self._position.value[1],
                                 cord + offset)

        return adjusted_position

    def _outermost_point(self, bounds: List[Point3D]) -> Point3D:
        """Find the outermost point in a Model.

        This method looks at the bounds of the actors and finds the outermost point
        in actors from a certain direction. For example, if you are looking at the model
        from top and you wished to know the outermost point in +Z, this method helps you
        find that point. This point is used in creating adjusted camera position when
        parallel projection is requested.

        Returns:
            A Ladybug Point3D object.
        """
        # Check axis(index) and direction to find the nearest point
        index, dir = self._flat_view_directions[self._direction.value]

        # dictionary with cordinate(int):Point3D structure
        cord_point = {point[index]: point for point in bounds}

        # if z-axis
        if index == 2:
            if dir == '+':
                outermost_point = cord_point[sorted(cord_point, reverse=True)[0]]
            else:
                outermost_point = cord_point[sorted(cord_point)[0]]
        # if x-axis or y-axis
        else:
            if dir == '+':
                outermost_point = cord_point[sorted(cord_point)[0]]
            else:
                outermost_point = cord_point[sorted(cord_point, reverse=True)[0]]

        return outermost_point

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
