"""A VTK camera object."""

import vtk
from honeybee_radiance.view import View
from honeybee.typing import clean_and_id_rad_string
from ._helper import _check_tuple


class Camera(View):
    """Create a vtk camera object.

        Args:
            identifier: A text string to be used as a name for the camera.
                Defaults to None.
            position: A tuple of three decimal values that represent the x, y and z
                coordinates of camera in a 3D space. Defaults to (0.0, 0.0, 25.0).
            direction: A tuple of three decimal values that represent the x, y, and z
                components of a vector towards the aim of the camera.
                Defaults to (0.0, 0.0, -1.0).
            up_vector: A tuple of three decimal values to represent the x, y, and z
                component of the vector that represents where the top of the camera is.
                Defaults to (0.0, 1.0, 0.0).
            h_size: A decimal value representing the horizontal view angle.
                Defaults to 60.0.
        """

    def __init__(self, identifier=None, position=None, direction=None,
                 up_vector=None, h_size=None):

        super().__init__(identifier=identifier, position=position, direction=direction,
                         up_vector=up_vector, h_size=h_size)
                         
        self.identifier = identifier
        self.position = position
        self.direction = direction
        self.up_vector = up_vector
        self.h_size = h_size

    @property
    def identifier(self):
        """Name of the camera object."""
        return self._identifier

    @identifier.setter
    def identifier(self, val):
        if not val:
            self._identifier = clean_and_id_rad_string('camera')
        else:
            self._identifier = clean_and_id_rad_string(val)

    @property
    def position(self):
        """Position of the camera."""
        return self._position

    @position.setter
    def position(self, val):
        if not val:
            self._position = (0.0, 0.0, 50.0)
        elif _check_tuple(val, float):
            self._position = val
        else:
            raise ValueError(
                f'The value must be a tuple with three decimal values. Instead got {val}'
            )

    @property
    def direction(self):
        """Vector representing the direction of the camera."""
        return self._direction

    @direction.setter
    def direction(self, val):
        if not val:
            self._direction = (0.0, 0.0, -1.0)
        elif _check_tuple(val, float):
            self._direction = val
        else:
            raise ValueError(
                f'The value must be a tuple with three decimal values. Instead got {val}'
            )

    @property
    def up_vector(self):
        """Vector that represents where the top of the camera is."""
        return self._up_vector

    @up_vector.setter
    def up_vector(self, val):
        if not val:
            self._up_vector = (0.0, 1.0, 0.0)
        elif _check_tuple(val, float):
            self._up_vector = val
        else:
            raise ValueError(
                f'The value must be a tuple with three decimal values. Instead got {val}'
            )

    @property
    def h_size(self):
        """Horizontal view angle."""
        return self._h_size

    @h_size.setter
    def h_size(self, val):
        if not val:
            self._h_size = 60.0
        elif isinstance(val, float):
            self._h_size = val
        else:
            raise ValueError(
                f'The value must be a decimal number. Instead got {val}.'
            )

    def to_vtk(self):
        """Get a vtk camera object."""
        camera = vtk.vtkCamera()
        # The location of camera in a 3D space
        camera.SetPosition(self._position)
        # The direction to the point where the camera is looking at
        camera.SetFocalPoint(self._direction)
        # Where the top of the camera is
        camera.SetViewUp(self._up_vector)
        # Horizontal view angle
        camera.SetViewAngle(self._h_size)
        camera.SetUseHorizontalViewAngle(True)
        camera.UseHorizontalViewAngleOn()
        return camera

    @classmethod
    def from_hbjson(cls, model):
        """Create camera objects from the radiance views in an hbjson model.

        Args:
            model: An hbjson model object.
        """
        pass

