"""A VTK scene."""

from __future__ import annotations

from typing import Dict, List, Tuple, Union

import vtk

from ._helper import _validate_input
from .actor import Actor
from .assistant import Assistant
from .camera import Camera
from .headless import try_headless
from .legend_parameter import LegendParameter
from .types import ImageTypes


class Scene:
    """Initialize a Scene object.

    Vtk derives inspiration from a movie set in naming its objects. Imagine a scene
    being prepared at a movie set. The scene has a background. It has a few actors, there
    are assistants running around making sure everything is ready, and there are a few
    cameras setup to capture the scene from different angles. A
    scene in vtk is defined in the similar fashion. It has a background color, some
    actors i.e. geometry objects from model, a few cameras around the scene, and
    assistants equal the number of cameras setup in the scene.

    Args:
        background_color: A tuple of three integers that represent RGB values of the
            color that you'd like to set as the background color. Defaults to gray.
    """

    def __init__(self, background_color: Tuple[int, int, int] = None) -> None:
        self.background_color = background_color
        self._actors = {}
        self._cameras = []
        self._assistants = []

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
    def actors(self) -> List[str]:
        """Name of actors in the scene."""
        return self._actors.keys()

    @property
    def cameras(self) -> List[Camera]:
        """A list of honeybee-vtk cameras setup in the scene."""
        return self._cameras

    @property
    def assistants(self) -> List[Assistant]:
        """A list of honeybee-vtk assistants working in the scene."""
        return self._assistants

    @property
    def legend_parameters(self) -> Dict[str, LegendParameter]:
        """Legends in the scene that can be added to the images."""
        legends_dict = {}
        for actor in self._actors.values():
            for legend_param in actor.legend_parameters:
                legends_dict[legend_param.name] = legend_param
        return legends_dict

    def legend_parameter(self, name: str) -> LegendParameter:
        """Get a legend parameter object by name.

        Args:
            name: A string for the name of the legend parameters you are looking for.

        Returns:
            A legend parameter object.
        """
        if name not in self.legend_parameters.keys():
            raise ValueError(
                'No legend parameter found by that name in this scene. The names of the'
                ' legend parameters in this scene are'
                f' {tuple(self.legend_parameters.keys())}.'
            )
        return self.legend_parameters[name]

    def add_cameras(self, val: Union[Camera, List[Camera]]) -> None:
        """Add a honeybee-vtk Camera objects to a Scene.

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
        """add honeybee-vtk Actor objects to a Scene.

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
        """Remove an actor from scene by name.

        Args:
            name: A string representing the name of the actor you would like to remove
                from the scene.
        """
        valid_names = tuple(['Aperture', 'Door', 'Shade', 'Wall', 'Floor', 'RoofCeiling',
                             'AirBoundary', 'Grid'])

        if name in valid_names:
            try:
                del self._actors[name]
            except KeyError:
                raise KeyError(
                    f'{name} is not found in the actors in this scene.')
        else:
            raise ValueError(
                'Name of the actors should be from one the following'
                f' values {valid_names}.'
            )

    def update_scene(self) -> None:
        """Update the scene.

        This method will use the latest cameras, actors, and visible legend parameters
        to create assistant object.
        """
        if self._cameras and self._actors:
            if self.legend_parameters:
                visible_legend_params = [
                    legend_param for legend_param in self.legend_parameters.values()
                    if legend_param.show_legend]
            else:
                visible_legend_params = []

            self._assistants = [
                Assistant(background_color=self._background_color, camera=camera,
                          actors=self._actors, legend_parameters=visible_legend_params)
                for camera in self._cameras]
        else:
            raise ValueError(
                'Add cameras and actors to the scene first.'
            )

    @try_headless
    def export_images(
            self, folder: str, name: str = 'Camera',
            image_type: ImageTypes = ImageTypes.png, *,
            image_scale: int = 1, image_width: int = 2000, image_height: int = 2000,
            color_range: vtk.vtkLookupTable = None, rgba: bool = False,
            show: bool = False) -> List[str]:
        """Export all the cameras in the scene as images.

        Reference: https://kitware.github.io/vtk-examples/site/Python/IO/ImageWriter/
        This method is able to export an image in '.png', '.jpg', '.ps', '.tiff', '.bmp',
        and '.pnm' formats.

        Args:
            folder: A valid path to where you'd like to write the images.
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

        Returns:
            A list of text strings representing the paths to the exported images.
        """
        self.update_scene()

        return [assistant._export_image(
            folder=folder, name=name + '_' + str(count), image_type=image_type,
            image_scale=image_scale, image_width=image_width, image_height=image_height,
            color_range=color_range, rgba=rgba, show=show)
            for count, assistant in enumerate(self._assistants)]

    def export_gltf(self, folder: str, name: str = 'Camera') -> str:
        """Export a scene to a glTF file.

        Args:
            folder: A valid path to where you'd like to write the gltf file.
            name: Name of the gltf file as a text string.

        Returns:
            A text string representing the path to the gltf file.
        """
        self.update_scene()

        if self._assistants:
            return self._assistants[0]._export_gltf(folder=folder, name=name)
        else:
            raise ValueError(
                'At least one camera needs to be setup to export an image.'
            )
