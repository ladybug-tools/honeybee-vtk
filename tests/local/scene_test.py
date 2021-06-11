"""Unit test for scene module."""


import pytest
import pathlib
import os
import shutil
import csv
from honeybee_vtk.model import Model
from honeybee_vtk.scene import Scene
from honeybee_vtk.vtkjs.schema import SensorGridOptions, DisplayMode
from honeybee_vtk.camera import Camera
from honeybee_vtk.actor import Actor
from honeybee_vtk.types import ImageTypes, Colors
from honeybee_vtk.legend_parameter import LabelFormat, Orientation


def test_export_images_from_view_file():
    """Test export images method using the from_view_file classmethod."""
    file_path = r'tests/assets/gridbased.hbjson'
    results_folder = r'tests/assets/df_results'
    target_folder = r'tests/assets/temp'
    view_file_path = r'tests/assets/view.vf'

    model = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Mesh)
    model.update_display_mode(DisplayMode.Wireframe)

    daylight_factor = []
    for grid in model.sensor_grids.data:
        res_file = pathlib.Path(results_folder, f'{grid.identifier}.res')
        grid_res = [float(v) for v in res_file.read_text().splitlines()]
        daylight_factor.append(grid_res)

    model.sensor_grids.add_data_fields(daylight_factor, name='Daylight-factor',
                                       per_face=True, data_range=(0, 20))
    model.sensor_grids.color_by = 'Daylight-factor'
    model.sensor_grids.display_mode = DisplayMode.SurfaceWithEdges

    # actors
    actors = Actor.from_model(model=model)

    # Initialize a scene
    scene = Scene(background_color=(255, 255, 255))
    scene.add_actors(actors)

    # A camera setup using the classmethod
    camera = Camera.from_view_file(file_path=view_file_path)

    # Add all the cameras to the scene
    scene.add_cameras(camera)

    # if target folder exists, delete it and create a fresh new folder
    if os.path.isdir(target_folder):
        shutil.rmtree(target_folder)
    os.mkdir(target_folder)

    # Export images for all the cameras
    images_path = scene.export_images(folder=target_folder, image_type=ImageTypes.png,
                                      name='camera')

    for path in images_path:
        assert os.path.isfile(path)

    shutil.rmtree(target_folder)


def test_export_images():
    """Test export images method."""
    file_path = r'tests/assets/gridbased.hbjson'
    results_folder = r'tests/assets/df_results'
    target_folder = r'tests/assets/temp'
    csv_path = r'tests/assets/radiation_results/radiation.csv'

    model = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Mesh)
    model.update_display_mode(DisplayMode.Wireframe)

    daylight_factor = []
    for grid in model.sensor_grids.data:
        res_file = pathlib.Path(results_folder, f'{grid.identifier}.res')
        grid_res = [float(v) for v in res_file.read_text().splitlines()]
        daylight_factor.append(grid_res)

    model.sensor_grids.add_data_fields(daylight_factor, name='Daylight-factor',
                                       per_face=True, data_range=(0, 20))
    model.sensor_grids.color_by = 'Daylight-factor'
    model.sensor_grids.display_mode = DisplayMode.SurfaceWithEdges

    radiation = []
    with open(csv_path) as csvfile:
        csvreader = csv.reader(csvfile)
        for data in csvreader:
            radiation.append([float(data[0])])

    model.shades.add_data_fields(radiation, name='Radiation', data_range=(0, 2000),
                                 colors=Colors.original)
    model.shades.color_by = 'Radiation'
    model.shades.display_mode = DisplayMode.SurfaceWithEdges

    # actors
    actors = Actor.from_model(model=model)

    # Initialize a scene
    scene = Scene(background_color=(255, 255, 255))
    scene.add_actors(actors)

    scene.legend_parameters['Daylight-factor'].orientation = Orientation.horizontal
    scene.legend_parameters['Daylight-factor'].show_legend = True
    scene.legend_parameters['Daylight-factor'].position = (0.0, 0.1)

    rd = scene.legend_parameter('Radiation')
    rd.orientation = Orientation.vertical
    rd.height = 0.45
    rd.width = 0.05
    rd.label_format = LabelFormat.integer
    rd.show_legend = True
    rd.position = (0.90, 0.1)

    # A camera setup using the constructor
    camera = Camera(position=(-50.28, -30.32, 58.64), direction=(0.59, 0.44, -0.67),
                    up_vector=(0.53, 0.40, 0.74), h_size=52.90)

    # Cameras extracted from hbjson
    cameras = model.cameras

    # Gather all the cameras
    cameras.append(camera)

    # Add all the cameras to the scene
    scene.add_cameras(cameras)

    # if target folder exists, delete it and create a fresh new folder
    if os.path.isdir(target_folder):
        shutil.rmtree(target_folder)
    os.mkdir(target_folder)

    # Export images for all the cameras
    images_path = scene.export_images(folder=target_folder, image_type=ImageTypes.png,
                                      name='camera')

    for path in images_path:
        assert os.path.isfile(path)

    shutil.rmtree(target_folder)
