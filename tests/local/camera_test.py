"""Unit tests for the camera module."""

import pytest
import vtk

from honeybee_vtk.camera import Camera


def test_to_vtk():
    "Test if default properties of the camera object."

    # Initialize a camera object and assess all the default properties
    camera = Camera()
    assert camera.identifier[0:6] == 'camera'
    assert camera.position.value == (0, 0, 100)
    assert camera.direction.value == (0, 0, -1)
    assert camera.up_vector.value == (0, 1, 0)
    assert camera.h_size.value == 60
    assert camera.v_size.value == 30
    assert camera.type.value == 'v'
    assert camera.flat_view_direction[(0, 0, -1)] == [2, '+']
    assert camera.flat_view_direction[(0, 0, 1)] == [2, '-']
    assert camera.flat_view_direction[(0, 1, 0)] == [1, '+']
    assert camera.flat_view_direction[(0, -1, 0)] == [1, '-']
    assert camera.flat_view_direction[(-1, 0, 0)] == [0, '-']
    assert camera.flat_view_direction[(1, 0, 0)] == [0, '+']

    # Assess type of the outcome of the to_vtk method
    camera = camera.to_vtk()
    assert isinstance(camera, vtk.vtkCamera)
