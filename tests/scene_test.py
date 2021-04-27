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
    model.update_display_mode(DisplayMode.Wireframe)

    scene = Scene(background_color=(0,0,0))
    scene.add_model(model)

    if os.path.isdir(target_folder):
        shutil.rmtree(target_folder)

    os.mkdir(target_folder)

    scene.to_gltf(target_folder, name='daylight-factor')

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
    assert isinstance(scene._interactor, vtk.vtkRenderWindowInteractor)
    assert isinstance(scene._window, vtk.vtkRenderWindow)
    assert isinstance(scene._renderer, vtk.vtkRenderer)
    with pytest.raises(ValueError):
        scene = Scene(background_color=(123.24, 23, 255))


def test_legend():
    """Test legend."""
    data_field = DataFieldInfo()
    color_range = data_field.color_range()
    scene = Scene()
    legend = scene.get_legend(color_range)
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
    scene = Scene()
    scene.add_model(model)
    assert scene._renderer.VisibleActorCount() == 6
