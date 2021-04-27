"""A VTK rendering scene."""
import pathlib
import enum
from typing import Tuple

import vtk

from .types import JoinedPolyData
from .model import Model, ModelDataSet, DisplayMode


class ImageTypes(enum.Enum):
    """Supported image types."""
    png = 'png'
    jpg = 'jpg'
    ps = 'ps'
    tiff = 'tiff'
    bmp = 'bmp'
    pnm = 'pnm'


class Scene(object):
    """A rendering scene with a single viewport.

    Once as scene is created you can export it to glTF, an image or just show it in an
    interactive viewer.

    """

    def __init__(self, background_color=None) -> None:
        """Initialize a Scene object.

        Args:
            background_color: A tuple of three floats that represent RGB values of the
                color that you'd like to set as the background color. Defaults to None.
        """
        super().__init__()
        interactor, window, renderer = self._create_render_window(background_color)
        self._renderer = renderer
        self._window = window
        self._interactor = interactor

    @staticmethod
    def _check_tuple(bg_color):
        """Check if all values in the tuple are integers.

        Args:
            bg_color: User input for background color

        Returns:
            A boolean value if True or None.
        """
        item_check = [isinstance(v, int) for v in bg_color]
        if item_check.count(True) == 3:
            return True

    def _create_render_window(self, background_color=None) \
            -> Tuple[
                vtk.vtkRenderWindowInteractor, vtk.vtkRenderWindow, vtk.vtkRenderer
            ]:
        """Create a rendering window with a single renderer and an interactor.

        The objects are embedded inside each other:
        interactor is the outmost layer. A render is added to a window and then the
        window is set inside the interactor.

        If you are thinking why, the answer is that is how VTK is designed to work.

        Args:
            background_color: A tuple of three floats that represent RGB values of the
                color that you'd like to set as the background color. Defaults to None.

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

        # Validate background color and set it for the render window
        if not background_color:
            colors = vtk.vtkNamedColors()
            background_color = colors.GetColor3d("SlateGray")

        elif isinstance(background_color, tuple) and len(background_color) == 3\
                and self._check_tuple(background_color):
            pass
        else:
            raise ValueError(
                'Background color is a tuple with three integers'
                ' representing R, G, and B values.'
            )

        renderer.SetBackground(background_color)
        renderer.TwoSidedLightingOn()

        # return the objects - the order is from outside to inside
        return interactor, window, renderer

    def get_legend(self, color_range) -> vtk.vtkScalarBarWidget():
        """Create a scalar bar widget.

        Args:
            color_range: A VTK LookUpTable object for color range. You can create one
                from color_range method in `DataFieldInfo`.
        Returns:
            A VTK scalar bar widget.
        """
        # create the scalar_bar
        scalar_bar = vtk.vtkScalarBarActor()
        scalar_bar.SetOrientationToHorizontal()
        scalar_bar.SetLookupTable(color_range)

        # create the scalar_bar_widget
        scalar_bar_widget = vtk.vtkScalarBarWidget()
        scalar_bar_widget.SetInteractor(self._interactor)
        scalar_bar_widget.SetScalarBarActor(scalar_bar)
        return scalar_bar_widget

    def add_model(self, model: Model):
        """Add a model to scene."""
        for ds in model:
            if ds.is_empty:
                continue
            self.add_dataset(ds)

    def add_dataset(self, data_set: ModelDataSet):
        """Create a dataset to scene as a VTK actor."""

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

        if data_set.edge_visibility:
            actor.GetProperty().EdgeVisibilityOn()

        if data_set.display_mode == DisplayMode.Wireframe:
            actor.GetProperty().SetRepresentationToWireframe()

        self._renderer.AddActor(actor)

    def to_gltf(self, folder, name):
        """Save the scene to a glTF file.

        Args:
            folder: A valid path to where you'd like to write the gltf file.
            name: Name of the gltf file as a text string.

        Returns:
            A text string representing the path to the gltf file.
        """
        gltf_file_path = pathlib.Path(folder, f'{name}.gltf')
        exporter = vtk.vtkGLTFExporter()
        exporter.SaveNormalOn()
        exporter.InlineDataOn()
        exporter.SetFileName(gltf_file_path.as_posix())
        exporter.SetActiveRenderer(self._renderer)
        exporter.SetRenderWindow(self._window)
        exporter.Modified()
        exporter.Write()
        return gltf_file_path.as_posix()

    @staticmethod
    def _get_image_writer(image_type: ImageTypes):
        """Get vtk image writer for each image type."""
        if image_type == ImageTypes.png:
            writer = vtk.vtkPNGWriter()
        elif image_type == ImageTypes.bmp:
            writer = vtk.vtkBMPWriter()
        elif image_type == ImageTypes.jpg:
            writer = vtk.vtkJPEGWriter()
        elif image_type == ImageTypes.pnm:
            writer = vtk.vtkPNMWriter()
        elif image_type == ImageTypes.ps:
            writer = vtk.vtkPostScriptWriter()
        elif image_type == ImageTypes.tiff:
            writer = vtk.vtkTIFFWriter()
        else:
            raise ValueError(f'Invalid image type: {image_type}')
        return writer

    def to_image(
        self, folder, name, image_type: ImageTypes = ImageTypes.png, *, rgba=True,
        image_scale=1, color_range=None, show=False
            ):
        """Save scene to an image.
        Reference: https://kitware.github.io/vtk-examples/site/Python/IO/ImageWriter/

        Args:
            folder: A valid path to where you'd like to write the image.
            name: Name of the image as a text string.
            image_type: An ImageType object
            rgba: A boolean value to set the type of buffer. A True value sets
                an RGBA buffer whereas a False value sets RGB buffer. Defaults to True.
            image_scale: An integer value as a scale factor. Defaults to 1.
            color_range: A vtk lookup table object which can be obtained
                from the color_range mehtod of the DataFieldInfo object. Defaults to None.
            show: A boolean value to decide if the the render window should pop up.
                Defaults to False.

        Returns:
            A text string representing the path to the image.
        """

        if color_range:
            scalar_bar = vtk.vtkScalarBarActor()
            scalar_bar.SetOrientationToHorizontal()
            scalar_bar.SetLookupTable(color_range)

            # create the scalar_bar_widget
            legend = vtk.vtkScalarBarWidget()
            legend.SetInteractor(self._interactor)
            legend.SetScalarBarActor(scalar_bar)
            legend.On()

        # render window
        if not show:
            self._window.OffScreenRenderingOn()
        self._window.Render()

        image_path = pathlib.Path(folder, f'{name}.{image_type.value}')
        writer = self._get_image_writer(image_type)

        window_to_image_filter = vtk.vtkWindowToImageFilter()
        window_to_image_filter.SetInput(self._window)
        window_to_image_filter.SetScale(image_scale)  # image quality

        # rgba is not supported for postscript image type
        if rgba and image_type != ImageTypes.ps:
            window_to_image_filter.SetInputBufferTypeToRGBA()
        else:
            window_to_image_filter.SetInputBufferTypeToRGB()
            # Read from the front buffer.
            window_to_image_filter.ReadFrontBufferOff()
            window_to_image_filter.Update()

        writer.SetFileName(image_path.as_posix())
        writer.SetInputConnection(window_to_image_filter.GetOutputPort())
        writer.Write()
        if color_range:
            legend.Off()

        return image_path.as_posix()

    # TODO: Color range input is a hack - we should keep track of the data
    # that is added to the scene and reuse them
    def show(self, color_range=None):
        """Show rendered view."""
        if color_range:
            legend = self.get_legend(color_range)
            legend.On()
        self._window.Render()
        self._interactor.Start()
        if color_range:
            legend.Off()
