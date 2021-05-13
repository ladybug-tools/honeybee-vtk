"""Vtk actors that are added to a vtk scene."""

import vtk
from .model import Model, ModelDataSet, DisplayMode
from .types import JoinedPolyData
from ._helper import _check_tuple
from ladybug_geometry.geometry3d.pointvector import Point3D


class Actors:
    """Create vtk actors from Model.

    Objects in Honeybee such as walls, floors, ceilings, shades, apertures, rooms are
    called actors in vtk terms. The actors are created from the Modeldatasets in a
    Model object.

    Args:
        model: A Model object created using honeybee-vtk Model.
            Defaults to None.
    """
    def __init__(self, model):
        self.model = model
        self._monochrome = False
        self._monochrome_color = (0.54, 0.54, 0.54)

    @property
    def model(self):
        """A honeybee-vtk Model object."""
        return self._model

    @model.setter
    def model(self, val: Model):
        if isinstance(val, Model):
            self._model = val
        else:
            raise ValueError(
                f'A {type(Model)} object created using honeybee-vtk required.'
                f' Instead got {type(val)}.'
            )

    @property
    def monochrome(self):
        """Whether to set actors to a monochrome color."""
        return self._monochrome

    @property
    def monochrome_color(self):
        """Default color to be used if actors are to be painted in a monochrome color."""
        return self._monochrome_color

    def set_to_monochrome(self, monochrome, monochrome_color=None):
        """Set monochrome colors for the actors.

        This is especially useful when the wireframe display-mode is being used.

        Args:
            monochrome: A boolean value. True value will set actors to a monochrome
                color.
            monochrome_color: A color that you'd like to paint actors with when
                monochrome is set to True. Defaults to None.
        """
        self._monochrome = monochrome
        if not monochrome_color:
            pass
        elif _check_tuple(monochrome_color, float, max_val=1.0):
            self._monochrome_color = monochrome_color
        else:
            raise ValueError(
                'monochrome color is a tuple with three decimal values less than 1'
                ' representing R, G, and B.'
            )

    def to_vtk(self):
        """Get a list of vtk actors from a Model object."""
        actors = []

        for ds in self._model:
            if ds.is_empty:
                continue
            actors.append(self._add_dataset(ds))

        return actors

    def _add_dataset(self, data_set: ModelDataSet):
        """Add a dataset to scene as a vtk actor.

        This method is only used in add_model method.

        Args:
            data_set: A ModelDataSet object from a Model object created using
                honeybee-vtk.

        Returns:
            A vtk actor object created from a dataset in model.
        """

        # calculate point data based on cell data
        cell_to_point = vtk.vtkCellDataToPointData()
        if len(data_set.data) > 1:
            polydata = JoinedPolyData.from_polydata(data_set.data)
            cell_to_point.SetInputConnection(polydata.GetOutputPort())
        else:
            polydata = data_set.data[0]
            cell_to_point.SetInputData(polydata)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(cell_to_point.GetOutputPort())

        # map cell data to pointdata
        if data_set.fields_info:
            field_info = data_set.active_field_info
            mapper.SetColorModeToMapScalars()
            mapper.SetScalarModeToUsePointData()
            mapper.SetScalarVisibility(True)
            range_min, range_max = field_info.data_range
            mapper.SetScalarRange(range_min, range_max)
            mapper.SetLookupTable(field_info.color_range())
            mapper.Update()

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)

        # Assign Ladybug Tools colors
        if self._monochrome:
            actor.GetProperty().SetColor(self._monochrome_color)
        else:
            actor.GetProperty().SetColor(data_set.rgb_to_decimal())

        if data_set.edge_visibility:
            actor.GetProperty().EdgeVisibilityOn()

        if data_set.display_mode == DisplayMode.Wireframe:
            actor.GetProperty().SetRepresentationToWireframe()

        return actor

    def get_bounds(self):
        """Get A list of Ladybug Point3D objects that represent the bounds of actors.

        Bounds of an actor are the outermost vertices of an actor. A bound is a tuple of
        x, y, and z coordinates."""

        points = []

        for actor in self.to_vtk():
            bound = actor.GetBounds()
            pt_min = Point3D(bound[0], bound[2], bound[4])
            pt_max = Point3D(bound[1], bound[3], bound[5])
            min_max = [pt_min, pt_max]
            points.extend(min_max)

        return points

        