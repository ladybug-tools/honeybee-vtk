"""A VTK camera object."""

import vtk
from math import tan, sin
from honeybee.typing import clean_and_id_rad_string
from ladybug_geometry.geometry3d.pointvector import Point3D
from ._helper import _check_tuple


class Camera:
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
            v_size: A decimal value representing the vertical view angle.
                Defaults to 60.0.
            view_type: Choose between a perspective and parallel view type. 'v' will set
                the perspective view and 'l' will set the parallel view. Defaults to 'v'
                which is the perspective view.
        """

    def __init__(self, identifier=None, position=None, direction=None,
                 up_vector=None, h_size=None, v_size=None, view_type=None):

        self.identifier = identifier
        self.position = position
        self.direction = direction
        self.up_vector = up_vector
        self.h_size = h_size
        self.v_size = v_size
        self.view_type = view_type

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

    @property
    def v_size(self):
        """Verical view angle."""
        return self._v_size

    @v_size.setter
    def v_size(self, val):
        if not val:
            self._v_size = 60.0
        elif isinstance(val, float):
            self._v_size = val
        else:
            raise ValueError(
                f'The value must be a decimal number. Instead got {val}.'
            )

    @property
    def view_type(self):
        """View type."""
        return self._view_type

    @view_type.setter
    def view_type(self, val):
        if not val:
            self.view_type = 'v'
        elif isinstance(val, str) and val.lower() in ['v', 'l']:
            self._view_type = val
        else:
            raise ValueError(
                f'Only "v" and "l" are accepted. Instead got {val}.'
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

        if self._view_type == 'l':
            camera.SetParallelProjection(True)
            camera.ParallelProjectionOn()
            # TODO: Setting parallel scale needs further look
            camera.SetParallelScale(self._v_size / 2)

        camera.SetUseHorizontalViewAngle(True)
        camera.UseHorizontalViewAngleOn()
        return camera

    @classmethod
    def from_model(cls, model):
        """Create camera objects from the radiance views in a Model object.

        Args:
            model: A Model object.

        Returns:
            A list of vtk camera objects.
        """
        if len(model.views) == 0:
            raise ValueError(
                'Either load_views was not set to True while create a honeybee-vtk Model'
                ' or no radiance views were found in the hbjson file.'
            )
        else:
            return [cls(position=view.position.value,
                    direction=view.direction.value,
                    up_vector=view.up_vector.value,
                    h_size=view.h_size.value,
                    v_size=view.v_size.value,
                    view_type=view.type.value).to_vtk() for view in model.views]
