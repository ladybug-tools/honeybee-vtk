"""Unit test for assistants module."""

import pytest
import vtk
from honeybee_vtk.assistant import Assistant
from honeybee_vtk.camera import Camera


def test_initialization():
    """Test objct initialization."""

    with pytest.raises(TypeError):
        assistant = Assistant()

    camera = Camera()
    assistant = Assistant(background_color=(0, 0, 0), camera=camera)
    assert isinstance(assistant._interactor, vtk.vtkRenderWindowInteractor)
    assert isinstance(assistant._window, vtk.vtkRenderWindow)
    assert isinstance(assistant._renderer, vtk.vtkRenderer)
