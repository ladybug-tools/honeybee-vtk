"""A VTK scene."""

from __future__ import annotations
import vtk
from typing import List, Tuple, Dict, Union
from ._helper import _validate_input
from .camera import Camera
from .actor import Actor


class Scene(object):
    """Initialize a Scene object.

    Vtk derives inspiration from a movie set in naming its objects. Imagine a scene
    being prepared at a movie set. The scene has a background. It has a few actors.
    And, there are a few cameras setup to capture the scene from different angles. A
    scene in vtk is defined in the similar fashion. It has a background color, some
    actors i.e. geometry objects from model, and a few cameras around the scene.

    Args:
        background_color: A tuple of three integers that represent RGB values of the
            color that you'd like to set as the background color. Defaults to gray.
    """
    def __init__(self, background_color: Tuple[int, int, int] = None) -> None:
        self.background_color = background_color
        self._actors = {}
        self._cameras = []

    @property
    def background_color(self) -> Tuple[int, int, int]:
        """background_color for the scene."""
        return self._background_color

    @background_color.setter
    def background_color(self, val: Tuple[int, int, int]) -> None:
        if not val:
            colors = vtk.vtkNamedColors()
            self._background_color = colors.GetColor3d("SlateGray")
        elif _validate_input(val, int):
            self._background_color = val
        else:
            raise ValueError(
                'Background color is a tuple with three integers'
                ' representing R, G, and B values.'
            )

    @property
    def actors(self) -> Dict[str, Actor]:
        """A dictionary of vtk actor name: vtk actor structure."""
        return self._actors

    @property
    def cameras(self) -> List[Camera]:
        """A list of vtk cameras setup in the scene."""
        return self._cameras

    def add_cameras(self, val: Union[Camera, List[Camera]]) -> None:
        """Add vtk Camera objects to a Scene.

        Args:
            val: Either a list of Camera objects or a single Camera object.
        """
        if isinstance(val, list) and _validate_input(val, Camera):
            self._cameras.extend(val)
        elif isinstance(val, Camera):
            self._cameras.append(val)
        else:
            raise ValueError(
                'Either a list of Camera objects or a Camera object is expected.'
                f' Instead got {val}.'
            )

    def add_actors(self, val: Union[Actor, List[Actor]]) -> None:
        """add vtk Actor objects to a Scene.

        Args:
            val: Either a list of Actors objects or a single Actor object.
        """
        if isinstance(val, list) and _validate_input(val, Actor):
            for v in val:
                self._actors[v.name] = v
        elif isinstance(val, Actor):
            self._actors[val.name] = val
        else:
            raise ValueError(
                'Either a list of Actor objects or an Actor object is expected.'
                f' Instead got {val}.'
            )

    def remove_actor(self, name: str) -> None:
        if name in ['Aperture', 'Door', 'Shade', 'Wall', 'Floor', 'RoofCeiling',
                    'AirBoundary', 'Grid']:
            try:
                del self._actors[name]
            except KeyError:
                raise KeyError(
                    f'{name} is not found in the actors attached to this scene.')

    def get_legend(
            self,
            color_range: vtk.vtkLookupTable,
            interactor: vtk.vtkRenderWindowInteractor) -> vtk.vtkScalarBarWidget():
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

    def export_images(
            self,
            folder: str,
            name: str,
            image_type: ImageTypes = ImageTypes.png,
            *,
            image_scale: int = 1,
            image_width: int = 2400,
            image_height: int = 2000,
            color_range: vtk.vtkLookupTable = None,
            rgba: bool = False) -> Tuple[str]:
        """Export all the cameras setup in a scene as images.

        This method calls export_image method under the hood.

        Args:
            folder: A valid path to where you'd like to write the images.
            name: A text string that will be used as a name for the images.
            image_type: An ImageType object.
            image_scale: An integer value as a scale factor. Defaults to 1.
            image_width: An integer value that sets the width of image in pixels.
            image_height: An integer value that sets the height of image in pixels.
            color_range: A vtk lookup table object which can be obtained
                from the color_range mehtod of the DataFieldInfo object.
                Defaults to None.
            rgba: A boolean value to set the type of buffer. A True value sets
                an the background color to black. A False value uses the Scene object's
                background color. Defaults to False.

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
