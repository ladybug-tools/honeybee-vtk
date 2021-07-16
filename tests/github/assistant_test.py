"""Unit test for assistants module."""

from honeybee_vtk.legend_parameter import LegendParameter
import pytest
import vtk
from honeybee_vtk.model import Model
from honeybee_vtk.assistant import Assistant
from honeybee_vtk.actor import Actor
from honeybee_vtk.camera import Camera
from honeybee_vtk.scene import Scene
from honeybee_vtk.vtkjs.schema import SensorGridOptions
from honeybee_vtk.config import load_config

file_path = r'tests/assets/gridbased.hbjson'
valid_json_path = r'tests/assets/config/valid.json'

model = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Sensors)
actors = Actor.from_model(model)
camera = Camera()
scene = Scene()
scene.add_actors(actors)
scene.add_cameras(camera)

load_config(valid_json_path, model, scene)

scene.update_scene()
assistant = scene.assistants[0]


def test_initialization():
    assert isinstance(assistant._actors, dict)
    assert isinstance(assistant._legend_params[0], LegendParameter)
    assert isinstance(assistant._camera, Camera)
    assert isinstance(assistant._background_color, vtk.vtkColor3d)


def test_create_window():
    interactor, window, renderer = assistant._create_window()
    assert isinstance(interactor, vtk.vtkRenderWindowInteractor)
    assert isinstance(window, vtk.vtkRenderWindow)
    assert isinstance(renderer, vtk.vtkRenderer)


def test_auto_image_dimension():
    image_width, image_height = assistant.auto_image_dimension()
    assert image_width == 512
    assert image_height == 512

    image_width, image_height = assistant.auto_image_dimension(2000, 2000)
    assert image_width == 2000
    assert image_height == 2000


def test_auto_text_height():
    image_width, image_height = assistant.auto_image_dimension()
    assert assistant._legend_params[0].label_parameters.size == 0
    assert assistant._legend_params[0].title_parameters.size == 0
    assistant.auto_text_height(image_width, image_height)
    assert assistant._legend_params[0].label_parameters.size == 13
    assert assistant._legend_params[0].title_parameters.size == 13
