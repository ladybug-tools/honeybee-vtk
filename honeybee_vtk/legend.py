"""Vtk legend object."""

import vtk
from typing import Tuple
from ._helper import _validate_input


class Legend:
    def __init__(self, name, color_set, range: Tuple[int, int] = (0, 100),
                 show_legend: bool = False, orientation: str = 'vertical',
                 location: Tuple[float, float] = (0.0, 0.0)
                ) -> None:

        self._name = name
        self._colors = color_set
        self._range = range
        self._show_legend = show_legend
        self.orientation = orientation
        self.position = location

    @property
    def name(self) -> str:
        return self._name

    @property
    def range(self) -> Tuple[float, float]:
        return self._range

    @property
    def show_legend(self) -> bool:
        """Visibility of the Legend object."""
        return self._show_legend

    @show_legend.setter
    def show_legend(self, val) -> None:
        if isinstance(val, bool):
            self._show_legend = val
        else:
            raise ValueError(
                'Only a True or False value is accepted.'
            )

    @property
    def orientation(self) -> str:
        return self._orientation

    @orientation.setter
    def orientation(self, val) -> None:
        if isinstance(val, str) and val.lower() in ['horizontal', 'vertical']:
            self._orientation = val.lower()
        else:
            raise ValueError(
                'Orientation accepts either "horizontal" or "vertical" as a value.'
            )

    @property
    def position(self) -> Tuple[float, float]:
        return self._position

    @position.setter
    def position(self, val) -> None:
        if isinstance(val, tuple) and _validate_input(val, float):
            self._position = val
        else:
            raise ValueError(
                'Location accepts a tuple of x and y coordinates in decimals.'
            )

    def get_lookuptable(self) -> vtk.vtkLookupTable:
        """Get a vtk lookuptable."""

        minimum, maximum = self._range
        color_values = self._colors
        lut = vtk.vtkLookupTable()
        lut.SetRange(minimum, maximum)
        lut.SetRampToLinear()
        lut.SetValueRange(minimum, maximum)
        lut.SetHueRange(0, 0)
        lut.SetSaturationRange(0, 0)
        print(color_values)
        lut.SetNumberOfTableValues(len(color_values))
        for count, color in enumerate(color_values):
            lut.SetTableValue(
                count, color.r / 255, color.g / 255, color.b / 255, color.a / 255
            )
        lut.Build()
        lut.SetNanColor(1, 0, 0, 1)
        return lut

    def get_scalarbar(self) -> vtk.vtkScalarBarActor:
        """Get a vtk scalar bar."""

        color_range = self.get_lookuptable()

        # create the scalarbar
        scalar_bar = vtk.vtkScalarBarActor()

        # set orientation
        if self._orientation == 'horizontal':
            scalar_bar.SetOrientationToHorizontal()
        else:
            scalar_bar.SetOrientationToVertical()

        # set location
        scalar_bar.SetPosition(self._position)

        # assign lookup table
        scalar_bar.SetLookupTable(color_range)

        scalar_bar.SetWidth(0.5)
        scalar_bar.SetHeight(0.05)
        return scalar_bar

    def __repr__(self) -> str:
        return f'Legend visibility: {self._show_legend}, Legend color scheme: '\
            f'{self._colors.name}, Legend range: {self._range}.'
