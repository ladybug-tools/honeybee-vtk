"""Vtk actors that are added to a vtk scene."""

from __future__ import annotations
import vtk
from typing import List, Tuple
from .model import Model, ModelDataSet, DisplayMode
from .types import JoinedPolyData
from ._helper import _validate_input
from ladybug_geometry.geometry3d.pointvector import Point3D
from .legend_parameter import LegendParameter


class Actor:
    """Create a vtk actor from a ModelDataSet.

    Objects in Honeybee such as walls, floors, ceilings, shades, apertures, rooms are
    called actors in vtk terms. The actors are created from the Modeldatasets in a
    Model object.

    Args:
        modeldataset: A ModelDataSet object from a honeybee-vtk Model.
    """

    def __init__(self, modeldataset: ModelDataSet) -> None:
        self.modeldataset = modeldataset
        self._name = self._modeldataset.name
        self._monochrome_color = None

    @property
    def modeldataset(self) -> ModelDataSet:
        """A honeybee-vtk Model object."""
        return self._modeldataset

    @modeldataset.setter
    def modeldataset(self, val: ModelDataSet) -> None:
        if isinstance(val, ModelDataSet):
            self._modeldataset = val
        else:
            raise ValueError(
                f'A {type(ModelDataSet)} object created using honeybee-vtk required.'
                f' Instead got {type(val)}.'
            )

    @property
    def name(self) -> str:
        return self._name

    @property
    def monochrome_color(self) -> Tuple[float, float, float]:
        """Color to be used if actors are to be painted in a monochrome color."""
        return self._monochrome_color

    @property
    def legend_parameters(self) -> List[LegendParameter]:
        """Legend parameters in the DataFieldInfo of ModelDataSet of this actor."""
        return [info.legend_parameter for info in self._modeldataset.fields_info.values()
                if info.legend_parameter]

    def get_monochrome(self, monochrome_color: Tuple[float, float, float]) -> None:
        """Get actors in monochrome color.

        This is especially useful when the wireframe display-mode is being used.

        Args:
            monochrome_color: A color that you'd like to paint actors with. Color here
                is a tuple of three decimal values representing R,G, and B.
        """
        if _validate_input(monochrome_color, float, max_val=1.0):
            self._monochrome_color = monochrome_color
        else:
            raise ValueError(
                'monochrome color is a tuple with three decimal values less than 1'
                ' representing R, G, and B.'
            )

    def to_vtk(self) -> vtk.vtkActor:
        """Create a vtk actor from a ModelDataSet object."""

        # calculate point data based on cell data
        cell_to_point = vtk.vtkCellDataToPointData()
        if len(self._modeldataset.data) > 1:
            polydata = JoinedPolyData.from_polydata(self._modeldataset.data)
            cell_to_point.SetInputConnection(polydata.GetOutputPort())
        else:
            polydata = self._modeldataset.data[0]
            cell_to_point.SetInputData(polydata)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(cell_to_point.GetOutputPort())

        # map cell data to pointdata
        if self._modeldataset.fields_info:
            field_info = self._modeldataset.active_field_info
            mapper.SetColorModeToMapScalars()
            mapper.SetScalarModeToUsePointData()
            mapper.SetScalarVisibility(True)

            range_min, range_max = field_info.legend_parameter.range
            mapper.SetScalarRange(range_min, range_max)
            mapper.SetLookupTable(field_info.legend_parameter.get_lookuptable())
            mapper.Update()

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)

        # Assign Ladybug Tools colors
        if self._monochrome_color:
            actor.GetProperty().SetColor(self._monochrome_color)
        else:
            actor.GetProperty().SetColor(self._modeldataset.rgb_to_decimal())

        if self._modeldataset.edge_visibility:
            actor.GetProperty().EdgeVisibilityOn()

        if self._modeldataset.display_mode == DisplayMode.Wireframe:
            actor.GetProperty().SetRepresentationToWireframe()

        return actor

    @classmethod
    def from_model(cls, model: Model) -> List[Actor]:
        """Create a list of vtk actors from a honeybee-vtk model.

        Args:
            model: A honeybee-vtk model.

        Returns:
            A list of vtk actors.
        """
        return [cls(modeldataset=ds) for ds in model if len(ds.data) > 0]

    @staticmethod
    def get_bounds(actors: List[Actor]) -> List[Point3D]:
        """Get a list of Ladybug Point3D objects that represent the bounds of actors.

        Bounds of an actor are the outermost vertices of an actor. A bound is a tuple of
        x, y, and z coordinates.

        Args:
            actors: A list of honeybee-vtk actor objects.

        Returns:
            A list of Ladybug Point3D objects.
        """

        points = []

        for actor in actors:
            vtk_actor = actor.to_vtk()
            bound = vtk_actor.GetBounds()
            pt_min = Point3D(bound[0], bound[2], bound[4])
            pt_max = Point3D(bound[1], bound[3], bound[5])
            min_max = [pt_min, pt_max]
            points.extend(min_max)

        return points

    @staticmethod
    def get_centroid(actors: List[Actor]) -> Point3D:
        """Get Centroid of actors.

        This method is used in CLI to create a default Top view camera for models that
        don't have any radiance views.

        Args:
            actors: A list of honeybee-vtk actor objects.

        Returns:
            Centroid as a Point3D object.
        """
        points = Actor.get_bounds(actors)

        x = sum([point.x for point in points]) / len(points)
        y = sum([point.y for point in points]) / len(points)
        z = sum([point.z for point in points]) / len(points)

        return Point3D(x, y, z)
