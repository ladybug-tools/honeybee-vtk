"""A VTK rendering scene."""
import pathlib
from typing import Tuple, Union

import vtk

from ladybug.color import Colorset


class Scene(object):
    """A rendering scene."""

    COLORSET = Colorset()

    def __init__(self, background_color=None) -> None:
        super().__init__()
        interactor, window, renderer = self._create_render_window(background_color)
        self._renderer = renderer
        self._window = window
        self._interactor = interactor

    def _create_render_window(self, background_color=None) \
            -> Tuple[
                vtk.vtkRenderWindowInteractor, vtk.vtkRenderWindow, vtk.vtkRenderer
            ]:
        """Create a rendering window with a single renderer and an interactor.

        The objects are embedded inside each other:
        interactor is the outmost layer. A render is added to a window and then the
        window is set inside the interactor.

        If you are thinking why, the answer is that is how VTK is designed to work.

        Returns:
            Tuple -- window_interactor, render_window, renderer
        """
        renderer = vtk.vtkRenderer()
        window = vtk.vtkRenderWindow()
        interactor = vtk.vtkRenderWindowInteractor()
        # add renderer to rendering window
        window.AddRenderer(renderer)
        # set rendering window in window interactor
        interactor.SetRenderWindow(window)

        if not background_color:
            colors = vtk.vtkNamedColors()
            background_color = colors.GetColor3d("SlateGray")
        renderer.SetBackground(background_color)
        renderer.TwoSidedLightingOn()
        # return the objects - the order is from outside to inside
        return interactor, window, renderer

    def _color_range_collection(self, index=1):
        """A VTK lookup table that acts as a color range."""
        color_values = self.COLORSET[index]
        lut = vtk.vtkLookupTable()
        lut.SetRange(0, 100)
        lut.SetRampToLinear()
        lut.SetValueRange(0, 100)
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

    def get_legend(self, color_range=None) -> vtk.vtkRenderWindowInteractor():
        """Add legend to an interactor.

        Returns:
            Renderer with an embedded legend.
        """
        # create the scalar_bar
        if not color_range:
            color_range = self._color_range_collection()
        scalar_bar = vtk.vtkScalarBarActor()
        scalar_bar.SetOrientationToHorizontal()
        scalar_bar.SetLookupTable(color_range)

        # create the scalar_bar_widget
        scalar_bar_widget = vtk.vtkScalarBarWidget()
        scalar_bar_widget.SetInteractor(self._interactor)
        scalar_bar_widget.SetScalarBarActor(scalar_bar)
        return scalar_bar_widget

    def add_object(
        self,
        polydata: Union[vtk.vtkPolyData, vtk.vtkAppendPolyData],
        color_range=None, representation=None
            ) -> vtk.vtkActor:
        """Create a mapper and add retune it as an actor.

        An actor can be added to the renderer.
        """
        if not color_range:
            color_range = self._color_range_collection()
        mapper = vtk.vtkPolyDataMapper()
        # calculate point data based on cell data
        cell_to_point = vtk.vtkCellDataToPointData()
        if isinstance(polydata, vtk.vtkPolyData):
            cell_to_point.SetInputData(polydata)
        else:
            cell_to_point.SetInputConnection(polydata.GetOutputPort())

        mapper.SetInputConnection(cell_to_point.GetOutputPort())

        # map cell data to pointdata
        mapper.SetColorModeToMapScalars()
        mapper.SetScalarModeToUsePointData()
        mapper.SetScalarVisibility(True)
        mapper.SetScalarRange(0, 100)
        mapper.SetLookupTable(color_range)
        mapper.Update()

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().EdgeVisibilityOn()
        if representation == 'wireframe':
            actor.GetProperty().SetRepresentationToWireframe()
        self._renderer.AddActor(actor)

    def to_gltf(self, target_folder, name):
        """Save the scene to a glTF file."""
        legend = self.get_legend()
        legend.On()
        gltf_file_path = pathlib.Path(target_folder, f'{name}.gltf')
        exporter = vtk.vtkGLTFExporter()
        exporter.SaveNormalOn()
        exporter.InlineDataOn()
        exporter.SetFileName(gltf_file_path.as_posix())
        exporter.SetActiveRenderer(self._renderer)
        exporter.SetRenderWindow(self._window)
        exporter.Modified()
        exporter.Write()
        legend.Off()
        return gltf_file_path.as_posix()

    # TODO: support different image types
    # add support for other image exporters - see the reference link for more information
    def to_jpeg(self, target_folder, file_name):
        """Save scene to an image.

        Reference: https://lorensen.github.io/VTKExamples/site/Python/IO/ImageWriter/
        """
        # for some reason calling the legend from another method causes an error
        color_range = self._color_range_collection()
        scalar_bar = vtk.vtkScalarBarActor()
        scalar_bar.SetOrientationToHorizontal()
        scalar_bar.SetLookupTable(color_range)

        # create the scalar_bar_widget
        legend = vtk.vtkScalarBarWidget()
        legend.SetInteractor(self._interactor)
        legend.SetScalarBarActor(scalar_bar)
        legend.On()
        # render window
        self._window.Render()
        jpeg_file_path = pathlib.Path(target_folder, file_name + ".jpeg")
        writer = vtk.vtkJPEGWriter()
        window_to_image_filter = vtk.vtkWindowToImageFilter()
        window_to_image_filter.SetInput(self._window)
        window_to_image_filter.SetScale(1)  # image quality
        window_to_image_filter.SetInputBufferTypeToRGB()
        # Read from the front buffer.
        window_to_image_filter.ReadFrontBufferOff()
        window_to_image_filter.Update()
        writer.SetFileName(jpeg_file_path.as_posix())
        writer.SetInputConnection(window_to_image_filter.GetOutputPort())
        writer.Write()
        legend.Off()
        return jpeg_file_path.as_posix()

    def show(self):
        """Show rendered view."""
        legend = self.get_legend()
        legend.On()
        self._window.Render()
        self._interactor.Start()
        legend.Off()

    def to_vtkjs(self):
        """Export this scene as a vtkjs file.

        This file can be opened in ParaView Glance viewer.
        """
        pass
