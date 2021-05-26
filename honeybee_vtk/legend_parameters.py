"""Vtk legend parameters object."""

import vtk
from typing import Tuple
from ladybug.color import Colorset


class LegendParameters:
    def __init__(self, colors: Colorset, range: Tuple[int, int]) -> None:
        self._colors = colors
        self._range = range

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

        lut.SetNumberOfTableValues(len(color_values))
        for count, color in enumerate(color_values):
            lut.SetTableValue(
                count, color.r / 255, color.g / 255, color.b / 255, color.a / 255
            )
        lut.Build()
        lut.SetNanColor(1, 0, 0, 1)
        return lut

    def get_legend_widget(
            self, interactor: vtk.vtkRenderWindowInteractor) -> vtk.vtkScalarBarWidget():
        """Create a scalar bar widget.

        Args:
            color_range: A VTK LookUpTable object for color range. You can create one
                from color_range method in `DataFieldInfo`.
            interactor: A vtk renderwindowinteractor object that can be created using
                the create_render_window method.

        Returns:
            A VTK scalar bar widget.
        """
        color_range = self.get_lookuptable()
        # create the scalar_bar
        scalar_bar = vtk.vtkScalarBarActor()
        scalar_bar.SetOrientationToHorizontal()
        scalar_bar.SetLookupTable(color_range)

        # create the scalar_bar_widget
        scalar_bar_widget = vtk.vtkScalarBarWidget()
        scalar_bar_widget.SetInteractor(interactor)
        scalar_bar_widget.SetScalarBarActor(scalar_bar)
        return scalar_bar_widget
