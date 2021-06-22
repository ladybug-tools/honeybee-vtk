"""Unit tests for the camera module."""

import pytest
import vtk
from ladybug_geometry.geometry3d.pointvector import Point3D
from honeybee_vtk.camera import Camera
from honeybee_vtk.model import Model
from honeybee_vtk.vtkjs.schema import SensorGridOptions
from honeybee_vtk.actor import Actor


def test_to_vtk():
    "Test if default properties of the camera object."

    # Initialize a camera object and assess all the default properties
    camera = Camera()
    assert camera.identifier[0:6] == 'camera'
    assert camera.position == (0, 0, 100)
    assert camera.direction == (0, 0, -1)
    assert camera.up_vector == (0, 1, 0)
    assert camera.h_size == 60
    assert camera.v_size == 30
    assert camera.type == 'v'
    assert camera.flat_view_direction[(0, 0, -1)] == [2, '+']
    assert camera.flat_view_direction[(0, 0, 1)] == [2, '-']
    assert camera.flat_view_direction[(0, 1, 0)] == [1, '+']
    assert camera.flat_view_direction[(0, -1, 0)] == [1, '-']
    assert camera.flat_view_direction[(-1, 0, 0)] == [0, '-']
    assert camera.flat_view_direction[(1, 0, 0)] == [0, '+']

    # Assess type of the outcome of the to_vtk method
    camera = camera.to_vtk()
    assert isinstance(camera, vtk.vtkCamera)


def test_no_view():
    """Test if views are being read from hbjson."""
    file_path = r'tests/assets/unnamed.hbjson'

    model = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Mesh)
    # Checking if valueerror is raised when from_model is called on a model with no views
    with pytest.warns(Warning):
        model = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Mesh)


def test_model_with_views():
    """Test if all the views in the model are being loaded as Camera objects."""
    file_path = r'tests/assets/gridbased.hbjson'
    model = Model.from_hbjson(file_path)
    assert len(model.cameras) == 6


def test_assign_bounds():
    """Test bounds assignment."""
    file_path = r'tests/assets/viewbased.hbjson'
    model = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Mesh)

    actors = Actor.from_model(model)
    bounds = Actor.get_bounds(actors)
    check = [isinstance(point, Point3D) for point in bounds]
    assert check.count(True) == len(bounds)


def test_adjustable_postion():
    """Test if correct adjustable position is being returned."""

    bounds = [Point3D(-7.00, -4.00, 1.00), Point3D(12.00, 9.00, 5.00),
              Point3D(-8.00, -4.00, 0.00), Point3D(13.00, 9.00, 5.00),
              Point3D(-8.00, -7.00, 0.00), Point3D(12.00, 20.00, 15.00),
              Point3D(-8.00, -4.00, 0.00), Point3D(13.00, 9.00, 0.00),
              Point3D(-8.00, -4.00, 3.00), Point3D(13.00, 9.00, 5.00)]
    camera = Camera(position=(0, 0, 5000), direction=(0, 0, -1))
    assert camera._outermost_point(bounds=bounds) == Point3D(12.00, 20.00, 15.00)
    assert camera._adjusted_position(bounds=bounds) == (0, 0, 16)


def test_from_view_file():
    """Test creation of a camera object from a Radiance view file."""
    vf = r'tests/assets/view.vf'
    camera = Camera.from_view_file(vf)
    assert isinstance(camera, Camera)
