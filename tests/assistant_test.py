"""Unit test for assistants module."""

from honeybee_vtk.scene import Scene
import pytest
import vtk
from honeybee_vtk.model import Model
from honeybee_vtk.assistant import Assistant
from honeybee_vtk.actor import Actor
from honeybee_vtk.camera import Camera


def test_initialization():
    """Test objct initialization."""

    file_path = r'./tests/assets/gridbased.hbjson'
    model = Model.from_hbjson(hbjson=file_path)
    actors = Actor.from_model(model=model)
    camera = Camera()
    scene = Scene()
    scene.add_actors(actors)
    scene.add_cameras(camera)
    assistant = Assistant(background_color=(0, 0, 0), camera=camera, actors=scene._actors)
    assert isinstance(assistant._interactor, vtk.vtkRenderWindowInteractor)
    assert isinstance(assistant._window, vtk.vtkRenderWindow)
    assert isinstance(assistant._renderer, vtk.vtkRenderer)
