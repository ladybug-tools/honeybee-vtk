from honeybee_vtk.write import write_vtk
import os
import zipfile


def test_write():
    file_path = './tests/assets/unnamed.hbjson'

    # Write with default settings
    zip_path = write_vtk(file_path)
    assert os.path.isfile(zip_path)
    zip_file = zipfile.ZipFile(zip_path)
    assert len(zip_file.namelist()) == 11

    # Write without grids
    zip_path = write_vtk(file_path, include_grids=False)
    assert os.path.isfile(zip_path)
    zip_file = zipfile.ZipFile(zip_path)
    assert len(zip_file.namelist()) == 7

    # Write without vectors
    zip_path = write_vtk(file_path, include_vectors=False)
    assert os.path.isfile(zip_path)
    zip_file = zipfile.ZipFile(zip_path)
    assert len(zip_file.namelist()) == 8

    # Write without grids & vectors
    zip_path = write_vtk(file_path, include_grids=False, include_vectors=False)
    assert os.path.isfile(zip_path)
    zip_file = zipfile.ZipFile(zip_path)
    assert len(zip_file.namelist()) == 6
