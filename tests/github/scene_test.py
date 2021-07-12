"""Unit test for scene module."""


import pytest
import pathlib
import os
import shutil
import vtk
import csv
from honeybee_vtk.model import Model
from honeybee_vtk.scene import Scene
from honeybee_vtk.vtkjs.schema import SensorGridOptions, DisplayMode
from honeybee_vtk.camera import Camera
from honeybee_vtk.actor import Actor
from honeybee_vtk.types import ImageTypes, ColorSets
from honeybee_vtk.legend_parameter import DecimalCount, Orientation


def test_class_initialization():
    """Test if the attributes of the class are set correctly."""

    scene = Scene(background_color=(255, 255, 255))

    # Check that decimal values not allowed in background color
    with pytest.raises(ValueError):
        scene = Scene(background_color=(123.24, 23, 255))

    # Check default values for cameras and actors
    assert not scene._cameras
    assert not scene._actors
    assert not scene._assistants


def test_properties():
    """Test properties of a scene."""
    file_path = r'tests/assets/gridbased.hbjson'
    model = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Mesh)
    actors = Actor.from_model(model=model)

    scene = Scene()
    scene.add_cameras(model.cameras)
    scene.add_actors(actors)

    assert isinstance(scene.background_color, vtk.vtkColor3d)

    assert len(scene.cameras) == 6
    for camera in scene.cameras:
        assert isinstance(camera, Camera)

    assert len(scene.actors) == 6
    for actor in scene.actors:
        assert isinstance(actor, str)


def test_scene_camera():
    "Test a scene constructed with a camera object."

    camera = Camera(position=(-50.28, -30.32, 58.64), direction=(0.59, 0.44, -0.67),
                    up_vector=(0.53, 0.40, 0.74), h_size=52.90)
    scene = Scene(background_color=(255, 255, 255))
    scene.add_cameras(camera)
    assert len(scene.cameras) == 1
    assert scene.cameras[0].position == (-50.28, -30.32, 58.64)


def test_add_cameras_from_model():
    """Test adding a list of cameras."""

    file_path = r'tests/assets/gridbased.hbjson'

    model = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Mesh)
    assert len(model.cameras) == 6

    cameras = model.cameras
    camera = Camera(position=(-50.28, -30.32, 58.64), direction=(0.59, 0.44, -0.67),
                    up_vector=(0.53, 0.40, 0.74), h_size=52.90)
    cameras.append(camera)

    scene = Scene(background_color=(255, 255, 255))
    scene.add_cameras(cameras)
    assert len(scene.cameras) == 7


def test_write_gltf():
    """Test if a gltf file can be successfully written."""

    file_path = r'tests/assets/gridbased.hbjson'
    results_folder = r'tests/assets/df_results'
    target_folder = r'tests/assets/temp'

    model = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Mesh)

    daylight_factor = []
    for grid in model.sensor_grids.data:
        res_file = pathlib.Path(results_folder, f'{grid.identifier}.res')
        grid_res = [float(v) for v in res_file.read_text().splitlines()]
        daylight_factor.append(grid_res)

    model.sensor_grids.add_data_fields(daylight_factor, name='Daylight-factor',
                                       per_face=True, data_range=(0, 20))
    model.sensor_grids.color_by = 'Daylight-factor'
    model.sensor_grids.display_mode = DisplayMode.SurfaceWithEdges
    model.update_display_mode(DisplayMode.Shaded)

    camera = Camera()
    actors = Actor.from_model(model=model)
    scene = Scene(background_color=(0, 0, 0))
    scene.add_actors(actors)
    scene.add_cameras(camera)

    if os.path.isdir(target_folder):
        shutil.rmtree(target_folder)
    os.mkdir(target_folder)

    scene.export_gltf(target_folder, name='daylight-factor')
    gltf_path = os.path.join(target_folder, 'daylight-factor.gltf')
    assert os.path.isfile(gltf_path)

    shutil.rmtree(target_folder)


def test_remove_actor():
    """Test removing an actor from a scene."""
    file_path = r'tests/assets/gridbased.hbjson'

    model = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Mesh)
    actors = Actor.from_model(model=model)

    scene = Scene()
    scene.add_actors(actors)
    scene.remove_actor('Shade')
    scene.add_cameras(model.cameras)
    assert 'Shade' not in scene.actors


def test_adding_data():
    """Test adding data to the model."""
    file_path = r'tests/assets/gridbased.hbjson'
    results_folder = r'tests/assets/df_results'

    model = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Mesh)

    # Get results
    daylight_factor = []
    for grid in model.sensor_grids.data:
        res_file = pathlib.Path(results_folder, f'{grid.identifier}.res')
        grid_res = [float(v) for v in res_file.read_text().splitlines()]
        daylight_factor.append(grid_res)

    model.sensor_grids.add_data_fields(daylight_factor, name='Daylight-factor',
                                       per_face=True, data_range=(0, 20))
    model.sensor_grids.color_by = 'Daylight-factor'
    model.sensor_grids.display_mode = DisplayMode.SurfaceWithEdges
    model.update_display_mode(DisplayMode.SurfaceWithEdges)

    assert 'Daylight-factor' in model.sensor_grids.fields_info.keys()
