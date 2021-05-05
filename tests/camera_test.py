"""Unit tests for the camera module."""

import pytest
import vtk
from honeybee_vtk.camera import Camera
from honeybee_vtk.model import Model
from honeybee_vtk.vtkjs.schema import SensorGridOptions


def test_from_model():
    """Test if views are being read from hbjson."""
    file_path = r'./tests/assets/viewbased.hbjson'

    model = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Mesh,
                              load_views=False)
    with pytest.raises(ValueError):
        camera = Camera.from_model(model)

    model = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Mesh,
                              load_views=True)
    cameras = Camera.from_model(model)
    cameras_check = [isinstance(camera, vtk.vtkCamera) for camera in cameras]
    assert cameras_check.count(True) == len(cameras)


