"""Vtk actors that are added to a vtk scene."""

import vtk
from honeybee.typing import clean_and_id_rad_string
from .model import Model, ModelDataSet, DisplayMode
from .types import JoinedPolyData
from ._helper import _check_tuple


class Actors:
    def __init__(self, cast_id=None, model=None, monochrome=None, monochrome_color=None):
        """Create vtk actors.

        Args:
            cast_id: A text string that will be used as an id for vtk actors. Defaults to None.
            model: A model object create using honeybee-vtk Model. Defaults to None.
            monochrome: A boolean value. If set to True, one color will be applied to all
                the geometry objects in Scene. This is especially useful when
                the DisplayMode is set to Wireframe and results are going to be
                loaded to the model.
            monochrome_color: A tuple of decimal numbers to represent RGB color.
                Defaults to gray.
        """
        self.cast_id = cast_id
        self.model = model
        self.monochrome = monochrome
        self.monochrome_color = monochrome_color
    
    @property
    def cast_id(self):
        """Id of actors."""
        return self._cast_id
    
    @cast_id.setter
    def cast_id(self, val):
        if not val:
            self._cast_id = clean_and_id_rad_string('camera')
        else:
            self._cast_id = clean_and_id_rad_string(val)

    @property
    def model(self):
        """A honeybee-vtk model."""
        return self._model

    @model.setter
    def model(self, val):
        if isinstance(val, Model):
            self._model = val
        elif not val:
            self._model = None
        else:
            raise ValueError(
                f'A Model object created using honeybee-vtk required. Instead got {val}.'
            )
    
    @property
    def monochrome(self):
        """Switch for monochrome colors."""
        return self._monochrome

    @monochrome.setter
    def monochrome(self, val):
        if not val:
            self._monochrome = False
        elif isinstance(val, bool):
            self._monochrome = val
        else:
            raise ValueError(
                f'A boolean value required. Instead got {val}.'
            )

    @property
    def monochrome_color(self):
        """Color to be used in monochrome mode."""
        return self._monochrome_color

    @monochrome_color.setter
    def monochrome_color(self, val):
        if not self._monochrome or not val:
            self._monochrome_color = (0.54, 0.54, 0.54)
        elif _check_tuple(val, float, max_val=1.0):
            self._monochrome_color = val
        else:
            raise ValueError(
                'monochrome color is a tuple with three decimal values less than 1'
                ' representing R, G, and B.'
            )

    def to_vtk(self):
        """Get a list of vtk actors from the model.

        Args:
            model: A Model camera object created using honeybee-vtk.

        Returns:
            A list of vtk actor objects created from the model.
        """
        actors = []

        for ds in self._model:
            if ds.is_empty:
                continue
            actors.append(self._add_dataset(ds))

        return actors

    def _add_dataset(self, data_set: ModelDataSet):
        """Add a dataset to scene as a VTK actor.

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
        """Get A list of points that represent the bounds of actors. Here, each point
        is a tuple of x, y, and z coordinates."""

        points = []

        for actor in self.to_vtk():
            bound = actor.GetBounds()
            pt_min = (bound[0], bound[2], bound[4])
            pt_max = (bound[1], bound[3], bound[5])
            min_max = [pt_min, pt_max]
            points.extend(min_max)

        return points

        