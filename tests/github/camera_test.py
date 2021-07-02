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

    # Assess type of the outcome of the to_vtk method
    camera = camera.to_vtk()
    assert isinstance(camera, vtk.vtkCamera)


def test_model_with_views():
    """Test if all the views in the model are being loaded as Camera objects."""
    file_path = r'tests/assets/gridbased.hbjson'
    model = Model.from_hbjson(file_path)
    assert len(model.cameras) == 6


def test_from_view_file():
    """Test creation of a camera object from a Radiance view file."""
    vf = r'tests/assets/view.vf'
    camera = Camera.from_view_file(vf)
    assert isinstance(camera, Camera)


def test_aerial_cameras():
    """Test creation of default aerial cameras."""
    file_path = r'tests/assets/revit_model/model.hbjson'
    model = Model.from_hbjson(file_path)
    actors = Actor.from_model(model)
    bounds = Actor.get_bounds(actors)
    centroid = Actor.get_centroid(actors)
    cameras = Camera.aerial_cameras(bounds, centroid)

    assert len(cameras) == 4

    def rounded(tup):
        return list(map(lambda x: round(x, 4), tup))

    cam_01, cam_02, cam_03, cam_04 = cameras
    assert rounded((cam_01.position)) == rounded(
        (124.35035099551129, 87.54659771487164, 56.45049285888672))
    assert rounded((cam_01.direction)) == rounded((-108.78812527224468, -
                                                   108.78812527224468, -41.03615807294845))
    assert cam_01.up_vector == (0.0, 0.0, 1.0)
    assert rounded((cam_02.position)) == rounded((-93.22589954897808,
                                                  87.54659771487164, 56.45049285888672))
    assert rounded((cam_02.direction)) == rounded((
        108.78812527224468, -108.78812527224468, -41.03615807294845))
    assert cam_02.up_vector == (0.0, 0.0, 1.0)
    assert rounded((cam_03.position)) == rounded((-93.22589954897808, -
                                                  130.02965282961773, 56.45049285888672))
    assert rounded((cam_03.direction)) == rounded((
        108.78812527224468, 108.78812527224468, -41.03615807294845))
    assert cam_03.up_vector == (0.0, 0.0, 1.0)
    assert rounded((cam_04.position)) == rounded((
        124.35035099551129, -130.02965282961773, 56.45049285888672))
    assert rounded((cam_04.direction)) == rounded((-108.78812527224468,
                                                   108.78812527224468, -41.03615807294845))
    assert cam_04.up_vector == (0.0, 0.0, 1.0)
