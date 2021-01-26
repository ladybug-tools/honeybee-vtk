from honeybee_vtk.writer import writer
import os
import zipfile


def test_write():
    file_path = './tests/assets/unnamed.hbjson'

    # Write with default settings
    zip_path = writer(file_path, writer='vtk', target_folder='./tests/assets/temp')
    assert os.path.isfile(zip_path)
    zip_file = zipfile.ZipFile(zip_path)
    assert len(zip_file.namelist()) == 6


def test_write_grids():
    file_path = './tests/assets/unnamed.hbjson'
    # Write without grids
    zip_path = writer(file_path, include_grids=True, writer='vtk',
                      target_folder='./tests/assets/temp')
    assert os.path.isfile(zip_path)
    zip_file = zipfile.ZipFile(zip_path)
    assert len(zip_file.namelist()) == 8


def test_write_vectors():
    file_path = './tests/assets/unnamed.hbjson'
    # Write without vectors
    zip_path = writer(file_path, include_sensors='vectors', writer='vtk',
                      target_folder='./tests/assets/temp')
    assert os.path.isfile(zip_path)
    zip_file = zipfile.ZipFile(zip_path)
    assert len(zip_file.namelist()) == 8


def test_write_no_grids_no_vectors():
    file_path = './tests/assets/unnamed.hbjson'
    # Write without grids & vectors
    zip_path = writer(file_path, writer='vtk', target_folder='./tests/assets/temp')
    assert os.path.isfile(zip_path)
    zip_file = zipfile.ZipFile(zip_path)
    assert len(zip_file.namelist()) == 6
