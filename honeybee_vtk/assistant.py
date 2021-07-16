"""An assistant class to the Scene object."""

import vtk
import pathlib
from typing import Tuple
from .actor import Actor
from .camera import Camera
from .types import ImageTypes


class Assistant:
    """Initialize an Assistant object.

    This is more of a helper class and the interface for this class is the Scene object.
    This class takes a camera and a list of actors to assemble a vtk interactor, a vtk
    renderWindow, and a vtk renderer objects.

    Args:
        background_color: A tuple of three integers that represent RGB values of the
            color that you'd like to set as the background color.
        actors: A dictionary of actors from a Scene object
        camera: A Camera object.
        legend_parameters: A list of legend parameter objects to be added to the scene
    """

    def __init__(self, background_color: Tuple[int, int, int], camera: Camera,
                 actors: dict, legend_parameters: list) -> None:

        self._background_color = background_color
        self._actors = actors
        self._camera = camera
        self._legend_params = legend_parameters

    def _create_window(self) -> None:
        """Create a rendering window with a single renderer and an interactor.

        The objects are embedded inside each other. interactor is the outmost layer.
        A render is added to a window and then the window is set inside the interactor.
        This method returns a tuple of a window_interactor, a render_window, and a
        renderer.

        Returns:
            A tuple with three elements

            -   interactor: A vtkRenderWindowInteractor object.

            -   window: A vtkRenderWindow object.

            -   renderer: A vtkRenderer object.

        """
        if not self._camera:
            raise ValueError(
                'A camera is needed to create a render window.'
            )

        # Setting renderer, render window, and interactor
        renderer = vtk.vtkRenderer()

        # Add actors to the window
        for actor in self._actors.values():
            renderer.AddActor(actor.to_vtk())

        # Add legends to the window
        if self._legend_params:
            for legend_param in self._legend_params:
                if not legend_param.hide_legend:
                    # Add legends to renderer
                    renderer.AddActor(legend_param.get_scalarbar())

        # add renderer to rendering window
        window = vtk.vtkRenderWindow()
        window.AddRenderer(renderer)

        # set rendering window in window interactor
        interactor = vtk.vtkRenderWindowInteractor()
        interactor.SetRenderWindow(window)

        # Set background color
        renderer.SetBackground(self._background_color)
        renderer.TwoSidedLightingOn()

        renderer.SetActiveCamera(self._camera.to_vtk())
        renderer.ResetCamera()

        # the order is from outside to inside
        return interactor, window, renderer

    def _export_gltf(self, folder: str, name: str) -> str:
        """Export a scene to a glTF file.

        Args:
            folder: A valid path to where you'd like to write the gltf file.
            name: Name of the gltf file as a text string.

        Returns:
            A text string representing the path to the gltf file.
        """
        # TODO: Find out why model's displaymode is not applied
        # TODO: Find out if the axis should be rotated to work with gltf viewers
        # TODO: Find a viewer for gltf files. The up axis of f3d viewer is Y axis.

        window, renderer = self._create_window()[1:]

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
    def _get_image_writer(image_type: ImageTypes) -> None:
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

    def auto_image_dimension(self, image_width: int = 0, image_height: int = 0) -> Tuple[int]:
        """Calculate image dimension.

        If image width and image height are not specified by the user, Camera's x and y
        dimension are used instead. Note that a Camera object gets x and y dimension from
        its parent Radiance View object.

        Args:
            image_width: Image width in pixels set by the user. Defaults to 0, which
                will use view's x dimension.
            image_height: Image height in pixels set by the user. Defaults to 0, which
                will use view's y dimension.

        Returns:
            A tuple with two elements

            -   image_width: Image width in pixels.

            -   image_height: Image height in pixels.
        """
        dim_x, dim_y = self._camera.dimension_x_y()
        if not image_width:
            image_width = dim_x
        if not image_height:
            image_height = dim_y

        return image_width, image_height

    def auto_text_height(self, image_width, image_height) -> None:
        """Calculate text height based on image dimension.

        If a user has not specified the text height in legend parameters, it will be
        calculated based on the average of image width and image height. 2.5% of this
        average is used as the text height.

        Args:
            image_width: Image width in pixels set by the user.
            image_height: Image height in pixels set by the user.
        """
        text_size = round(((image_width + image_height) / 2) * 0.025)

        for legend_param in self._legend_params:
            if legend_param.label_parameters.size == 0:
                legend_param.label_parameters.size = text_size
            if legend_param.title_parameters.size == 0:
                legend_param.title_parameters.size = text_size

    def _export_image(
            self, folder: str, image_type: ImageTypes = ImageTypes.png, *,
            image_scale: int = 1, image_width: int = 0, image_height: int = 0,
            color_range: vtk.vtkLookupTable = None, rgba: bool = False,
            show: bool = False) -> str:
        """Export the window as an image.

        Reference: https://kitware.github.io/vtk-examples/site/Python/IO/ImageWriter/
        This method is able to export an image in '.png', '.jpg', '.ps', '.tiff', '.bmp',
        and '.pnm' formats.

        Args:
            folder: A valid path to where you'd like to write the image.
            image_type: An ImageType object.
            image_scale: An integer value as a scale factor. Defaults to 1.
            image_width: An integer value that sets the width of image in pixels.
                Defaults to 0, which will use view's x dimension.
            image_height: An integer value that sets the height of image in pixels.
                Defaults to 0, which will use view's y dimension.
            color_range: A vtk lookup table object which can be obtained
                from the color_range mehtod of the DataFieldInfo object.
                Defaults to None.
            rgba: A boolean value to set the type of buffer. A True value sets
                an the background color to black. A False value uses the Scene object's
                background color. Defaults to False.
            show: A boolean value to decide if the the render window should pop up.
                Defaults to False.
            legends: Legends to add to the image.

        Returns:
            A text string representing the path to the image.
        """
        # Set image width and height
        image_width, image_height = self.auto_image_dimension(image_width, image_height)

        # Set text height for the labels and the title of the legend
        self.auto_text_height(image_width, image_height)

        # Create a render window
        interactor, window = self._create_window()[:2]

        # render window
        if not show:
            window.OffScreenRenderingOn()
            window.SetSize(image_width, image_height)
            window.Render()
        else:
            window.SetSize(image_width, image_height)
            window.Render()
            interactor.Initialize()
            interactor.Start()

        image_path = pathlib.Path(
            folder, f'{self._camera.identifier}.{image_type.value}')
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

        return image_path.as_posix()
