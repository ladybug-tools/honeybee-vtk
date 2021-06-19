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
        camera: A Camera object.
        actors: A dictionary of actors from a Scene object
        legend_parameters: A list of legend parameter objects to be added to the scene
    """

    def __init__(self, background_color: Tuple[int, int, int], camera: Camera,
                 actors: dict, legend_parameters: list) -> None:

        self._background_color = background_color
        self._actors = actors
        self._camera = camera
        self._interactor = None
        self._window = None
        self._renderer = None
        self._legend_params = legend_parameters
        self._create_window()

    def _create_window(self) -> None:
        """Create a rendering window with a single renderer and an interactor.

        The objects are embedded inside each other. interactor is the outmost layer.
        A render is added to a window and then the window is set inside the interactor.
        This method returns a tuple of a window_interactor, a render_window, and a
        renderer.
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
        self._interactor, self._window, self._renderer = (interactor, window, renderer)

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

    def _export_image(
            self, folder: str, name: str, image_type: ImageTypes = ImageTypes.png, *,
            image_scale: int = 1, image_width: int = 2000, image_height: int = 2000,
            color_range: vtk.vtkLookupTable = None, rgba: bool = False,
            show: bool = False) -> str:
        """Export the window as an image.

        Reference: https://kitware.github.io/vtk-examples/site/Python/IO/ImageWriter/
        This method is able to export an image in '.png', '.jpg', '.ps', '.tiff', '.bmp',
        and '.pnm' formats.

        Args:
            folder: A valid path to where you'd like to write the image.
            name: Name of the image as a text string.
            image_type: An ImageType object.
            image_scale: An integer value as a scale factor. Defaults to 1.
            image_width: An integer value that sets the width of image in pixels.
                Defaults to 2000.
            image_height: An integer value that sets the height of image in pixels.
                Defaults to 2000.
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

        # render window
        if not show:
            self._window.OffScreenRenderingOn()
            self._window.SetSize(image_width, image_height)
            self._window.Render()
        else:
            self._window.SetSize(image_width, image_height)
            self._window.Render()
            self._interactor.Initialize()
            self._interactor.Start()

        image_path = pathlib.Path(folder, f'{name}.{image_type.value}')
        writer = self._get_image_writer(image_type)
        if image_type == ImageTypes.jpg:
            writer.SetQuality(100)  # image quality

        window_to_image_filter = vtk.vtkWindowToImageFilter()
        window_to_image_filter.SetInput(self._window)
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
