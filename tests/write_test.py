from honeybee_vtk.writer import writer
import os
import zipfile


def test_write():
    file_path = './tests/assets/unnamed.hbjson'

    # Write with default settings
    zip_path = writer(file_path, writer='vtk')
    assert os.path.isfile(zip_path)
    zip_file = zipfile.ZipFile(zip_path)
    assert len(zip_file.namelist()) == 11

    # Write without grids
    zip_path = writer(file_path, include_grids=False, writer='vtk')
    assert os.path.isfile(zip_path)
    zip_file = zipfile.ZipFile(zip_path)
    assert len(zip_file.namelist()) == 7

    # Write without vectors
    zip_path = writer(file_path, include_vectors=False, writer='vtk')
    assert os.path.isfile(zip_path)
    zip_file = zipfile.ZipFile(zip_path)
    assert len(zip_file.namelist()) == 8

    # Write without grids & vectors
    zip_path = writer(file_path, include_grids=False, include_vectors=False,
                      writer='vtk')
    assert os.path.isfile(zip_path)
    zip_file = zipfile.ZipFile(zip_path)
    assert len(zip_file.namelist()) == 6
