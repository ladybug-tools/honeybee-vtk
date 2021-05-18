"""A vtk render window."""

from __future__ import annotations
import vtk
from typing import List, Tuple


class Window:
    def __init__(self, actors=None, camera=None):
        self._actors = actors
        self._camera = camera

    def create_window(self) -> Tuple[
            vtk.vtkRenderWindowInteractor, vtk.vtkRenderWindow, vtk.vtkRenderer]:

        """Create a rendering window with a single renderer and an interactor.

        The objects are embedded inside each other. interactor is the outmost layer.
        A render is added to a window and then the window is set inside the interactor.
        This method returns a tuple of a window_interactor, a render_window, and a
        renderer.
        """
        # if camera is not provided use the first camera in the list of cameras setup
        # in the scene
        if not self._camera:
            

        # Setting renderer, render window, and interactor
        renderer = vtk.vtkRenderer()

        # Add actors to the window if model(actor) has arrived at the scene
        if self._actors:
            for actor in self._actors.values():
                renderer.AddActor(actor.to_vtk())
        else:
            warnings.warn('Actors should be added to this scene.')

        # add renderer to rendering window
        window = vtk.vtkRenderWindow()
        window.AddRenderer(renderer)

        # set rendering window in window interactor
        interactor = vtk.vtkRenderWindowInteractor()
        interactor.SetRenderWindow(window)

        # Set background color
        renderer.SetBackground(self._background_color)
        renderer.TwoSidedLightingOn()

        # Assign camera to the renderer
        if camera.type == 'v':
            renderer.SetActiveCamera(camera.to_vtk())
        else:
            bounds = Actor.get_bounds(self.actors.values())
            renderer.SetActiveCamera(camera.to_vtk(bounds=bounds))

        # return the objects - the order is from outside to inside
        return interactor, window, renderer
