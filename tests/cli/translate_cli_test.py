import os
from zipfile import ZipFile
from click.testing import CliRunner
from honeybee_vtk.cli import translate_recipe
from ladybug.futil import nukedir


# def test_write_html():
#     """Check whether an HTML file can be exported."""
#     runner = CliRunner()
#     file_path = './tests/assets/unnamed.hbjson'

#     result = runner.invoke(translate_recipe, [file_path])
#     assert result.exit_code == 0
#     assert os.path.isfile('unnamed.html')
#     os.remove('unnamed.html')


# def test_write_vtk():
#     """Check whether VTK files can be exported."""
#     runner = CliRunner()
#     file_path = './tests/assets/unnamed.hbjson'

#     result = runner.invoke(translate_recipe, [file_path, '--file-type', 'vtk'])
#     assert result.exit_code == 0
#     assert os.path.isfile('unnamed.zip')
#     with ZipFile('unnamed.zip', 'r') as zip_obj:
#         files = zip_obj.namelist()
#         vtks = ['vtk' == file[-3:] for file in files]
#         assert len(files) == vtks.count(True)
#     os.remove('unnamed.zip')
    

# def test_write_xml():
#     """Check whether XML files can be exported."""
#     runner = CliRunner()
#     file_path = './tests/assets/unnamed.hbjson'

#     result = runner.invoke(translate_recipe, [file_path, '--file-type', 'xml'])
#     assert result.exit_code == 0
#     assert os.path.isfile('unnamed.zip')
#     with ZipFile('unnamed.zip', 'r') as zip_obj:
#         files = zip_obj.namelist()
#         vtks = ['vtp' == file[-3:] for file in files]
#         assert len(files) == vtks.count(True)
#     os.remove('unnamed.zip')


# def test_file_name():
#     """Check whether a use selected name can be given to the file being exported."""
#     runner = CliRunner()
#     file_path = './tests/assets/unnamed.hbjson'

#     result = runner.invoke(translate_recipe, [file_path, '--name', 'test'])
#     assert result.exit_code == 0
#     assert os.path.isfile('test.html')
#     os.remove('test.html')


# def test_target_folder():
#     """Check whether a file can be exported to a target folder."""
#     runner = CliRunner()
#     file_path = './tests/assets/unnamed.hbjson'
#     target_path = './tests/assets/target'

#     os.mkdir(target_path)
#     result = runner.invoke(translate_recipe, [file_path, '--folder', target_path])
#     assert result.exit_code == 0
#     html_path = os.path.join(target_path, 'unnamed.html')
#     assert os.path.isfile(html_path)
#     nukedir(target_path, True)


# def test_grids():
#     """Check whether grids are exported."""
#     runner = CliRunner()
#     file_path = './tests/assets/unnamed.hbjson'

#     result = runner.invoke(translate_recipe, [file_path, '--include-grids',
#                                               '--file-type', 'vtk'])
#     assert result.exit_code == 0
#     assert os.path.isfile('unnamed.zip')
#     with ZipFile('unnamed.zip', 'r') as zip_obj:
#         files = zip_obj.namelist()
#         assert 'Grid base.vtk' in files
#         assert 'Grid mesh.vtk' in files
#     os.remove('unnamed.zip')


# def test_sensors_vectors():
#     """Check whether grid normals are exported as vectors."""
#     runner = CliRunner()
#     file_path = './tests/assets/unnamed.hbjson'

#     result = runner.invoke(translate_recipe, [
#         file_path, '--file-type', 'vtk', '--include-sensors', 'vectors'])
#     assert result.exit_code == 0
#     assert os.path.isfile('unnamed.zip')
#     with ZipFile('unnamed.zip', 'r') as zip_obj:
#         files = zip_obj.namelist()
#         assert 'Grid base vectors.vtk' in files
#         assert 'Grid mesh vectors.vtk' in files
#     os.remove('unnamed.zip')


# def test_sensors_points():
#     """Check whether grid normals are exported as color-grouped points."""
#     runner = CliRunner()
#     file_path = './tests/assets/unnamed.hbjson'

#     result = runner.invoke(translate_recipe, [
#         file_path, '--file-type', 'vtk', '--include-sensors', 'points'])
#     assert result.exit_code == 0
#     assert os.path.isfile('unnamed.zip')
#     with ZipFile('unnamed.zip', 'r') as zip_obj:
#         files = zip_obj.namelist()
#         assert 'Grid base points.vtk' in files
#         assert 'Grid mesh points.vtk' in files
#     os.remove('unnamed.zip')


# def test_aperture_vectors():
#     """Check whether aperture normals are exported as vectors."""
#     runner = CliRunner()
#     file_path = './tests/assets/unnamed.hbjson'

#     result = runner.invoke(translate_recipe, [
#         file_path, '--file-type', 'vtk', '--include-normals', 'vectors'])
#     assert result.exit_code == 0
#     assert os.path.isfile('unnamed.zip')
#     with ZipFile('unnamed.zip', 'r') as zip_obj:
#         files = zip_obj.namelist()
#         assert 'Aperture vectors.vtk' in files
#     os.remove('unnamed.zip')


# def test_aperture_points():
#     """Check whether aperture normals are exported as color-grouped points."""
#     runner = CliRunner()
#     file_path = './tests/assets/unnamed.hbjson'

#     result = runner.invoke(translate_recipe, [
#         file_path, '--file-type', 'vtk', '--include-normals', 'points'])
#     assert result.exit_code == 0
#     assert os.path.isfile('unnamed.zip')
#     with ZipFile('unnamed.zip', 'r') as zip_obj:
#         files = zip_obj.namelist()
#         assert 'Aperture points.vtk' in files
#     os.remove('unnamed.zip')
    