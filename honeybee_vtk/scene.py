"""A VTK scene."""

import pathlib
import enum
from typing import Tuple

import vtk

from .types import JoinedPolyData
from .model import Model, ModelDataSet, DisplayMode
from ._helper import _check_tuple
from .camera import Camera


class ImageTypes(enum.Enum):
    """Supported image types."""
    png = 'png'
    jpg = 'jpg'
    ps = 'ps'
    tiff = 'tiff'
    bmp = 'bmp'
    pnm = 'pnm'


class Scene(object):
    """Initialize a Scene object.

    Vtk derives inspiration from a movie set in naming its objects. Imagine a scene
    being prepared at a movie set. The scene has a background. It has a few actors.
    And, there are a few cameras setup to capture the scene from different angles. A
    scene is vtk is defined in the similar fashion. It has a background color, some
    actors i.e. geometry objects from model, and a few cameras around the scene.

    Args:
        background_color: A tuple of three integers that represent RGB values of the
            color that you'd like to set as the background color. Defaults to gray.
        model: A Model camera object created using honeybee-vtk.
        cameras: A list of vtk camera objects. Defaults to one camera that shows the
            scene from top.
        monochrome: A boolean value. If set to True, one color will be applied to all
            the geometry objects in Scene. This is especially useful when
            the DisplayMode is set to Wireframe and results are going to be
            loaded to the model.
        monochrome_color: A tuple of decimal numbers to represent RGB color.
            Defaults to gray.
    """
    __slots__ = ('_background_color', '_model', '_cameras', '_monochrome',
                 '_monochrome_color')

    def __init__(self, background_color=None, model=None, cameras=None, monochrome=None,
                 monochrome_color=None) -> None:

        self.background_color = background_color
        self.model = model
        self.cameras = cameras
        self.monochrome = monochrome
        self.monochrome_color = monochrome_color

    @property
    def background_color(self):
        """background_color for the scene."""
        return self._background_color

    @background_color.setter
    def background_color(self, val):
        if not val:
            colors = vtk.vtkNamedColors()
            self._background_color = colors.GetColor3d("SlateGray")
        elif _check_tuple(val, int):
            self._background_color = val
        else:
            raise ValueError(
                'Background color is a tuple with three integers'
                ' representing R, G, and B values.'
            )

    @property
    def model(self):
        """Model object to be added to the scene which will turn into actors."""
        return self._model

    @model.setter
    def model(self, val):
        if isinstance(val, Model):
            self._model = val
        elif not val:
            self._model = None
        else:
            raise ValueError(
                f'A Model object created using honeybee-vtk required. Intead got {val}.'
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

    @property
    def cameras(self):
        """A list of vtk cameras setup in the scene."""
        return self._cameras

    @cameras.setter
    def cameras(self, val):
        """Set up cameras

        Note: The scene object has one camera with perspective view by default.
        If you use this method to set a single camera or a list of cameras then
        the default camera will be removed. If you wish to preserve the default
        camera then initialize a Scene object without setting cameras and then
        use add_cameras method.

        Args:
            val: A single vtk camera object or a list of vtk camera objects.
        """
        if isinstance(val, list) and _check_tuple(val, vtk.vtkCamera):
            self._cameras = val
        elif isinstance(val, vtk.vtkCamera):
            self._cameras = [val]
        elif not val:
            camera = Camera()
            self._cameras = [camera.to_vtk()]
        else:
            raise ValueError(
                'Either a list of vtk camera objects or a vtk camera object is expected.'
                f' Instead got {val}. Make sure to use to_vtk method.'
            )

    def add_cameras(self, val):
        """Add vtk camera objects to a scene object.

        Args:
            val: Either a list of vtk camera objects or a single vtk camera object.
        """
        if isinstance(val, list) and _check_tuple(val, vtk.vtkCamera):
            self._cameras.extend(val)
        elif isinstance(val, vtk.vtkCamera):
            self._cameras.append(val)
        else:
            raise ValueError(
                'Either a list of vtk camera objects or a vtk camera object is expected.'
                f' Instead got {val}. Make sure to use to_vtk method.'
            )

    def create_render_window(self, camera=None) \
        -> Tuple[
            vtk.vtkRenderWindowInteractor, vtk.vtkRenderWindow, vtk.vtkRenderer
        ]:
        """Create a rendering window with a single renderer and an interactor.

        The objects are embedded inside each other. interactor is the outmost layer.
        A render is added to a window and then the window is set inside the interactor.

        Args:
            camera: A vtk camera object.

        Returns:
            A tuple of following;

            -   window_interactor,
            -   render_window,
            -   renderer
        """
        # if camera is not provided use the first camera in the list of cameras setup
        # in the scene
        if not camera:
            camera = self._cameras[0]
        elif isinstance(camera, vtk.vtkCamera):
            pass
        else:
            raise ValueError(
                f'The camera must be a vtk camera object. Instead got {camera}. Make'
                ' sure to use the to_vtk method once a camera is created.'
            )

        # Setting renderer, render window, and interactor
        renderer = vtk.vtkRenderer()
        renderer.SetActiveCamera(camera)

        # Add actors to the window if model(actor) has arrived at the scene
        if self._model:
            self.add_model(self._model, renderer)

        # add renderer to rendering window
        window = vtk.vtkRenderWindow()
        window.AddRenderer(renderer)

        # set rendering window in window interactor
        interactor = vtk.vtkRenderWindowInteractor()
        interactor.SetRenderWindow(window)

        # Set background color
        renderer.SetBackground(self._background_color)
        renderer.TwoSidedLightingOn()

        # return the objects - the order is from outside to inside
        return interactor, window, renderer

    def get_legend(self, color_range, interactor) -> vtk.vtkScalarBarWidget():
        """Create a scalar bar widget.

        Args:
            color_range: A VTK LookUpTable object for color range. You can create one
                from color_range method in `DataFieldInfo`.
            interactor: A vtk renderwindowinteractor object that can be created using
                the create_render_window method.

        Returns:
            A VTK scalar bar widget.
        """
        # create the scalar_bar
        scalar_bar = vtk.vtkScalarBarActor()
        scalar_bar.SetOrientationToHorizontal()
        scalar_bar.SetLookupTable(color_range)

        # create the scalar_bar_widget
        scalar_bar_widget = vtk.vtkScalarBarWidget()
        scalar_bar_widget.SetInteractor(interactor)
        scalar_bar_widget.SetScalarBarActor(scalar_bar)
        return scalar_bar_widget

    def add_model(self, model: Model, renderer):
        """Add a model to the scene.

        Args:
            model: A Model camera object created using honeybee-vtk.
            renderer: A vtk renderer object created using create_render_window method.
        """
        for ds in model:
            if ds.is_empty:
                continue
            self._add_dataset(ds, renderer)

    def _add_dataset(self, data_set: ModelDataSet, renderer):
        """Add a dataset to scene as a VTK actor.

        This method is only used in add_model method.

        Args:
            data_set: A ModelDataSet object from a Model object created using
                honeybee-vtk.
            renderer: A vtk renderer object created using create_render_window method.
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

        renderer.AddActor(actor)

    def export_gltf(self, folder, renderer, window, name):
        """Export a scene to a glTF file.

        Args:
            folder: A valid path to where you'd like to write the gltf file.
            renderer: A vtk renderer object created using create_render_window method.
            window: A vtk rendererwindow object created using
                create_render_window method.
            name: Name of the gltf file as a text string.

        Returns:
            A text string representing the path to the gltf file.
        """
        # TODO: Find out why model's displaymode is not applied
        # TODO: Find out if the axis should be rotated to work with gltf viewers
        # TODO: Find a viewer for gltf files. The up axis of f3d viewer is Y axis.

        gltf_file_path = pathlib.Path(folder, f'{name}.gltf')
        exporter = vtk.vtkGLTFExporter()
        exporter.SaveNormalOn()
        exporter.InlineDataOn()
        exporter.SetFileName(gltf_file_path.as_posix())
        exporter.SetActiveRenderer(renderer)
        exporter.SetRenderWindow(window)
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

    def export_image(self, folder, name, window, interactor,
                     image_type: ImageTypes = ImageTypes.png,
                     *, rgba=False, image_scale=1, image_width=2400, image_height=2000,
                     color_range=None, show=False):
        """Export the scene as an image.

        Reference: https://kitware.github.io/vtk-examples/site/Python/IO/ImageWriter/
        This method is able to export an image in '.png', '.jpg', '.ps', '.tiff', '.bmp',
        and '.pnm' formats.

        Args:
            folder: A valid path to where you'd like to write the image.
            name: Name of the image as a text string.
            window: A vtk rendererwindow object created using
                create_render_window method.
            interactor: A vtk renderwindowinteractor object created using
                create_render_window method.
            image_type: An ImageType object.
            rgba: A boolean value to set the type of buffer. A True value sets
                an the background color to black. A False value uses the Scene object's
                background color. Defaults to False.
            image_scale: An integer value as a scale factor. Defaults to 1.
            image_width: An integer value that sets the width of image in pixels.
            image_height: An integer value that sets the height of image in pixels.
            color_range: A vtk lookup table object which can be obtained
                from the color_range mehtod of the DataFieldInfo object.
                Defaults to None.
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
            legend.SetInteractor(interactor)
            legend.SetScalarBarActor(scalar_bar)
            legend.On()

        # render window
        if not show:
            window.OffScreenRenderingOn()
            window.SetSize(image_width, image_height)
            window.Render()
        else:
            window.SetSize(width, height)
            window.Render()
            interactor.Initialize()
            interactor.Start()

        image_path = pathlib.Path(folder, f'{name}.{image_type.value}')
        writer = self._get_image_writer(image_type)
        if image_type == ImageTypes.jpg:
            writer.SetQuality(100)  # image quality

        window_to_image_filter = vtk.vtkWindowToImageFilter()
        window_to_image_filter.SetInput(window)
        window_to_image_filter.SetScale(image_scale)

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

    def export_images(
        self, folder, name, image_type: ImageTypes = ImageTypes.png, *, rgba=False,
        image_scale=1, image_width=2400, image_height=2000, color_range=None
            ):
        """Export all the cameras setup in a scene as images.

        This method calls export_image method under the hood.

        Args:
            folder: A valid path to where you'd like to write the images.
            name: A text string that will be used as a name for the images.
            image_type: An ImageType object.
            rgba: A boolean value to set the type of buffer. A True value sets
                an the background color to black. A False value uses the Scene object's
                background color. Defaults to False.
            image_scale: An integer value as a scale factor. Defaults to 1.
            image_width: An integer value that sets the width of image in pixels.
            image_height: An integer value that sets the height of image in pixels.
            color_range: A vtk lookup table object which can be obtained
                from the color_range mehtod of the DataFieldInfo object.
                Defaults to None.

        Returns:
            A tuple of paths to each exported image.
        """
        file_paths = []

        for count, camera in enumerate(self._cameras):
            # Create a render window for each camera setup in the scene.
            interactor, window = self.create_render_window(camera)[0:2]
            file_paths.append(
                self.export_image(folder=folder, name=name + '_' + str(count),
                                  window=window, interactor=interactor,
                                  image_type=image_type, rgba=rgba,
                                  image_scale=image_scale, image_width=image_width,
                                  image_height=image_height, color_range=color_range)
                                  )
        return tuple(file_paths)
