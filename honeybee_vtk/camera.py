"""A VTK camera object."""

import vtk
from honeybee.typing import clean_and_id_rad_string
from ladybug_geometry.geometry3d.pointvector import Point3D


class Camera:
    """Create a vtk camera object.

        Args:
            identifier: A text string to be used as a name for the camera.
                Defaults to None.
            position: A tuple of three numbers that represent the x, y and z
                coordinates of camera in a 3D space. Defaults to (0.0, 0.0, 25.0).
            direction: A tuple of three numbers that represent the x, y, and z
                components of a vector towards the aim of the camera.
                Defaults to (0.0, 0.0, -1.0).
            up_vector: A tuple of three numbers to represent the x, y, and z
                component of the vector that represents where the top of the camera is.
                Defaults to (0.0, 1.0, 0.0).
            h_size: A number representing the horizontal view angle.
                Defaults to 60.0.
            v_size: A number representing the vertical view angle.
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
        elif isinstance(val, tuple) and len(val) == 3:
            self._position = val
        else:
            raise ValueError(
                'The value must be a tuple with three numbers representing x, y, and z'
                f' coordinates. Instead got {val}.'
            )

    @property
    def direction(self):
        """Vector representing the direction of the camera."""
        return self._direction

    @direction.setter
    def direction(self, val):
        if not val:
            self._direction = (0.0, 0.0, -1.0)
        elif isinstance(val, tuple) and len(val) == 3:
            self._direction = val
        else:
            raise ValueError(
                'The value must be a tuple with three numbers representing x, y, and z'
                f' components of a vector. Instead got {val}.'
            )

    @property
    def up_vector(self):
        """Vector that represents where the top of the camera is."""
        return self._up_vector

    @up_vector.setter
    def up_vector(self, val):
        if not val:
            self._up_vector = (0.0, 1.0, 0.0)
        elif isinstance(val, tuple) and len(val) == 3:
            self._up_vector = val
        else:
            raise ValueError(
                'The value must be a tuple with three numbers representing x, y, and z'
                f' components of a vector. Instead got {val}.'
            )

    @property
    def h_size(self):
        """Horizontal view angle."""
        return self._h_size

    @h_size.setter
    def h_size(self, val):
        if not val:
            self._h_size = 60.0
        elif val:
            self._h_size = val
        else:
            raise ValueError(
                f'The value must be a number. Instead got {val}.'
            )

    @property
    def v_size(self):
        """Verical view angle."""
        return self._v_size

    @v_size.setter
    def v_size(self, val):
        if not val:
            self._v_size = 60.0
        elif val:
            self._v_size = val
        else:
            raise ValueError(
                f'The value must be a number. Instead got {val}.'
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

    def to_vtk(self, bounds=None):
        """Get a vtk camera object."""
        camera = vtk.vtkCamera()

        if self._view_type == 'l':
            # Get bounds if flat a flat view is requested
            if self._direction in [(0, 0, -1), (0, 0, 1), (1, 0, 0),
                                   (-1, 0, 0), (0, 1, 0), (0, -1, 0)] and not bounds:
                raise ValueError(
                    'Bounds of actors are required to generate one of the flat views.'
                    ' Use get_bounds method of the Actors object to get these bounds.'
                )

            # get adjusted camera position
            adjusted_position = self.adjusted_position(bounds, self._position, self._direction)

            # The location of camera in a 3D space
            camera.SetPosition(adjusted_position)

            # get a focal_point on the same axis as the camera position. This is
            # necessary for flat views
            fp = (self._position[0]+self._direction[0],
                  self._position[1]+self._direction[1],
                  self._position[2]+self._direction[2])

            # The direction to the point where the camera is looking at
            camera.SetFocalPoint(fp)
            camera.SetParallelProjection(True)
            # TODO: Need to find a better way to set parallel scale
            camera.SetParallelScale(self._v_size)
            camera.ParallelProjectionOn()
        else:
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

    def adjusted_position(self, bounds):
        # Create Ladybug Point object
        position = Point3D(self._position[0], self._position[1], self._position[2])
        print(self._direction)
        # If the camera is looking in the Z direction
        if self._direction[2]:
            points_to_check = [Point3D(point[0], point[1], point[2]) for point in
                               bounds if point[2]]
            distance_to_position = [position.distance_to_point(point) for point
                                    in points_to_check]
            points_distance = dict(zip(distance_to_position, points_to_check))
            sorted_distances = [distance for distance in sorted(points_distance.keys())]
            nearest_point_z_cord = points_distance[sorted_distances[0]].z
            factor = 3
            adjusted_position = (self._position[0], self._position[1],
                                 nearest_point_z_cord+factor)
            return adjusted_position

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
