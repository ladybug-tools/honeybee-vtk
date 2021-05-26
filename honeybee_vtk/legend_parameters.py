"""Vtk legend parameters object."""

import vtk
from typing import Tuple
from ladybug.color import Colorset

COLORSET = Colorset()


class LegendParameters:
    def __init__(self, colors: Colorset = COLORSET.ecotect(),
                 range: Tuple[int, int] = (0, 100)) -> None:
        self._colors = colors
        self._range = range

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
