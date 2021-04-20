
import os
import shutil
from honeybee_vtk.model import Model
from honeybee_vtk.vtkjs.schema import SensorGridOptions


def test_write():
    file_path = './tests/assets/unnamed.hbjson'
    # Write with default settings
    model = Model.from_hbjson(file_path, load_grids=SensorGridOptions.Mesh)
    # zip_path = writer(file_path, writer='vtk', target_folder='./tests/assets/temp')
    target_folder = './tests/assets/temp'
    if os.path.isdir(target_folder):
        shutil.rmtree(target_folder)
    os.mkdir(target_folder)
    model.to_html(folder=target_folder, name='Model')
    html_path = os.path.join(target_folder, 'Model.html')
    assert os.path.isfile(html_path)
    shutil.rmtree(target_folder)


# def test_write_grids():
#     file_path = './tests/assets/unnamed.hbjson'
#     # Write without grids
#     zip_path = writer(file_path, include_grids=True, writer='vtk',
#                       target_folder='./tests/assets/temp')
#     assert os.path.isfile(zip_path)
#     zip_file = zipfile.ZipFile(zip_path)
#     assert len(zip_file.namelist()) == 8


# def test_write_vectors():
#     file_path = './tests/assets/unnamed.hbjson'
#     # Write without vectors
#     zip_path = writer(file_path, include_sensors='vectors', writer='vtk',
#                       target_folder='./tests/assets/temp')
#     assert os.path.isfile(zip_path)
#     zip_file = zipfile.ZipFile(zip_path)
#     assert len(zip_file.namelist()) == 8


# def test_write_no_grids_no_vectors():
#     file_path = './tests/assets/unnamed.hbjson'
#     # Write without grids & vectors
#     zip_path = writer(file_path, writer='vtk', target_folder='./tests/assets/temp')
#     assert os.path.isfile(zip_path)
#     zip_file = zipfile.ZipFile(zip_path)
#     assert len(zip_file.namelist()) == 6
