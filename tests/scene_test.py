"""Unit test for scene module."""

import pytest
import pathlib
import os
import shutil
import vtk
from honeybee_vtk.model import Model
from honeybee_vtk.scene import Scene, ImageTypes
from honeybee_vtk.vtkjs.schema import SensorGridOptions, DisplayMode
from honeybee_vtk.types import DataFieldInfo
from honeybee_vtk.camera import Camera
from honeybee_vtk.actors import Actors


def test_write_gltf():
    """Test if a gltf file can be successfully written."""

    file_path = r'./tests/assets/gridbased.hbjson'
    results_folder = r'./tests/assets/df_results'
    target_folder = r'./tests/assets/temp'

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

    actors = Actors("gltf", model)
    scene = Scene(background_color=(0,0,0), actors=actors.to_vtk())
    window, renderer = scene.create_render_window()[1:]

    if os.path.isdir(target_folder):
        shutil.rmtree(target_folder)
    os.mkdir(target_folder)

    scene.export_gltf(target_folder, renderer, window, name='daylight-factor')
    gltf_path = os.path.join(target_folder, 'daylight-factor.gltf')
    assert os.path.isfile(gltf_path)
    shutil.rmtree(target_folder)


def test_image_types():
    """Tests all the image types."""

    assert ImageTypes.png.value == 'png'
    assert ImageTypes.jpg.value == 'jpg'
    assert ImageTypes.ps.value == 'ps'
    assert ImageTypes.tiff.value == 'tiff'
    assert ImageTypes.bmp.value == 'bmp'
    assert ImageTypes.pnm.value == 'pnm'


def test_class_initialization():
    """Test if the attributes of the class are set correctly."""

    scene = Scene(background_color=(255, 255, 255))
  
    # Check that decimal values not allowed in background color
    with pytest.raises(ValueError):
        scene = Scene(background_color=(123.24, 23, 255))

    # Check a vtk camera object is attached by default
    assert isinstance(scene.cameras[0], vtk.vtkCamera)


def test_legend():
    """Test legend."""

    data_field = DataFieldInfo()
    color_range = data_field.color_range()
    scene = Scene()
    interactor = scene.create_render_window()[0]
    legend = scene.get_legend(color_range, interactor)
    assert isinstance(legend, vtk.vtkScalarBarWidget)


def test_actors_in_scene():
    """Test if all the dataset in a model are being added to the scene."""

    file_path = r'./tests/assets/gridbased.hbjson'
    model = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Mesh)

    # Test the number of non-empty datasets in the model
    non_empty_datasets = 0
    for dataset in model:
        if not dataset.is_empty:
            non_empty_datasets += 1
    assert non_empty_datasets == 6

    # Test that all the non-empty datasets are being added to the scene

    actors = Actors(model=model).to_vtk()
    scene = Scene(actors=actors)
    renderer = scene.create_render_window()[2]
    assert renderer.VisibleActorCount() == 6


def test_scene_camera():
    "Test a scene constructed with a camera object."

    camera = Camera(position=(-50.28, -30.32, 58.64), direction=(0.59, 0.44, -0.67),
                    up_vector=(0.53, 0.40, 0.74), h_size=52.90)
    scene = Scene(background_color=(255, 255, 255), cameras=camera.to_vtk())
    assert len(scene.cameras) == 1


def test_scene_cameras():
    """Test a scene constructed with a list of camera objects."""

    file_path = r'./tests/assets/viewbased.hbjson'
    model = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Mesh,
                              load_views=True)
    cameras = Camera.from_model(model)
    scene = Scene(background_color=(255, 255, 255), cameras=cameras)
    assert len(scene.cameras) == 1


def test_add_cameras():
    """Test adding a list of cameras."""

    file_path = r'./tests/assets/viewbased.hbjson'
    model = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Mesh)
    # Check is valuerror is raised in case the radiance views are not loaded on model
    with pytest.raises(ValueError):
        cameras = Camera.from_model(model)

    # Check the number of cameras extracted hbjson
    model = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Mesh,
                              load_views=True)
    cameras = Camera.from_model(model)
    assert len(cameras) == 1

    camera = Camera(position=(-50.28, -30.32, 58.64), direction=(0.59, 0.44, -0.67),
                    up_vector=(0.53, 0.40, 0.74), h_size=52.90)
    scene = Scene(background_color=(255, 255, 255))

    # Adding a list of camera objects
    cameras.append(camera.to_vtk())
    scene.add_cameras(cameras)
    assert len(scene.cameras) == 3


def test_add_camera():
    """Test adding a camera."""

    camera = Camera(position=(-50.28, -30.32, 58.64), direction=(0.59, 0.44, -0.67),
                    up_vector=(0.53, 0.40, 0.74), h_size=52.90)
    scene = Scene(background_color=(255, 255, 255))

    scene.add_cameras(camera.to_vtk())
    assert len(scene.cameras) == 2


# # The following two tests don't pass on Github and hence are kep off for now.

def test_export_image():
    """Test export images method."""
    file_path = r'./tests/assets/gridbased.hbjson'
    results_folder = r'./tests/assets/df_results'
    target_folder = r'./tests/assets/temp1'

    model = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Mesh,
                              load_views=True)

    daylight_factor = []
    for grid in model.sensor_grids.data:
        res_file = pathlib.Path(results_folder, f'{grid.identifier}.res')
        grid_res = [float(v) for v in res_file.read_text().splitlines()]
        daylight_factor.append(grid_res)

    model.sensor_grids.add_data_fields(daylight_factor, name='Daylight-factor',
                                       per_face=True, data_range=(0, 20))
    model.sensor_grids.color_by = 'Daylight-factor'
    model.sensor_grids.display_mode = DisplayMode.SurfaceWithEdges
    model.update_display_mode(DisplayMode.Wireframe)

    # Setup legend
    color_range = model.sensor_grids.active_field_info.color_range()

    # actors
    actors = Actors(model=model).to_vtk()

    # Initialize a scene
    scene = Scene(background_color=(255, 255, 255), actors=actors)

    # Create a camera Parallel projection camera using the constructor
    camera = Camera(position=(-50.28, -30.32, 58.64), direction=(0.59, 0.44, -0.67),
                    up_vector=(0.53, 0.40, 0.74), h_size=52.90, view_type='l').to_vtk()

    # Create a rendering window using the camera defined above
    interactor, window = scene.create_render_window(camera=camera)[0:2]

    # if target folder exists, delete it and create a fresh new folder
    if os.path.isdir(target_folder):
        shutil.rmtree(target_folder)
    os.mkdir(target_folder)

    # Export images for all the cameras
    path = scene.export_image(
        folder=target_folder, window=window, interactor=interactor,
        image_type=ImageTypes.png, name='camera', color_range=color_range, image_scale=2)

    assert os.path.isfile(path)
    shutil.rmtree(target_folder)


def test_export_images():
    """Test export images method."""
    file_path = r'./tests/assets/gridbased.hbjson'
    results_folder = r'./tests/assets/df_results'
    target_folder = r'./tests/assets/temp'

    model = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Mesh,
                              load_views=True)

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

    # Setup legend
    color_range = model.sensor_grids.active_field_info.color_range()

    # actors
    actors = Actors(model=model).to_vtk()

    # Initialize a scene
    scene = Scene(actors=actors, background_color=(255, 255, 255),
                  monochrome=False, monochrome_color=(0.0, 0.0, 0.0))

    # A camera setup using the constructor
    camera = Camera(position=(-50.28, -30.32, 58.64), direction=(0.59, 0.44, -0.67),
                    up_vector=(0.53, 0.40, 0.74), h_size=52.90)

    # Cameras extracted from hbjson
    cameras = Camera.from_model(model)

    # Gather all the cameras
    cameras.append(camera.to_vtk())

    # Add all the cameras to the scene
    scene.add_cameras(cameras)

    # if target folder exists, delete it and create a fresh new folder
    if os.path.isdir(target_folder):
        shutil.rmtree(target_folder)
    os.mkdir(target_folder)

    # Export images for all the cameras
    images_path = scene.export_images(folder=target_folder, image_type=ImageTypes.png,
                                      name='camera', color_range=color_range)

    for path in images_path:
        assert os.path.isfile(path)

    shutil.rmtree(target_folder)
