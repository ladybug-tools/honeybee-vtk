"""Unit tests for the camera module."""

import pytest
import vtk
from honeybee_vtk.camera import Camera
from honeybee_vtk.model import Model
from honeybee_vtk.vtkjs.schema import SensorGridOptions
from honeybee_vtk.actors import Actors


def test_to_vtk():
    "Test if default properties of the camera object coming out of to_vtk."

    # Initialize a camera object and assess all the default properties
    camera = Camera()
    assert camera.identifier[0:6] == 'camera'
    assert camera.position == (0, 0, 50)
    assert camera.direction == (0, 0, -1)
    assert camera.up_vector == (0, 1, 0)
    assert camera.h_size == 60
    assert camera.v_size == 60
    assert camera.view_type == 'v'

    # Assess type of the outcome of the to_vtk method
    camera = camera.to_vtk()
    assert isinstance(camera, vtk.vtkCamera)


def test_from_model():
    """Test if views are being read from hbjson."""
    file_path = r'./tests/assets/viewbased.hbjson'
    model = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Mesh)

    # Checking if valueerror is raised when from_model is called on a model with no views
    with pytest.raises(ValueError):
        camera = Camera.from_model(model)

    model = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Mesh,
                              load_views=True)

    cameras = Camera.from_model(model)
    cameras_check = [isinstance(camera, vtk.vtkCamera) for camera in cameras]
    assert cameras_check.count(True) == len(cameras)


def test_adjusted_camera():
    """Test creation of adjusted camera."""
    file_path = r'./tests/assets/gridbased.hbjson'
    model = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Mesh)
    bounds = Actors(model=model).get_bounds()
    adjusted_camera = Camera().adjusted_position(bounds)


    