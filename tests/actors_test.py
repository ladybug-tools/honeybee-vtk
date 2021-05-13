"""Unit test for actors module."""

import pytest
import vtk
from honeybee_vtk.actors import Actors
from honeybee_vtk.model import Model
from ladybug_geometry.geometry3d.pointvector import Point3D


def test_class_initialization():
    """Test default properties of a Actors object."""

    with pytest.raises(TypeError):
        actors = Actors()

    file_path = r'./tests/assets/gridbased.hbjson'
    model = Model.from_hbjson(file_path)
    actors = Actors(model)
    assert not actors.monochrome
    assert actors.monochrome_color == (0.54, 0.54, 0.54)


def test_monochrome():
    """Test setting actors to monochrome colors."""
    file_path = r'./tests/assets/gridbased.hbjson'
    model = Model.from_hbjson(file_path)
    actors = Actors(model)
    actors.set_to_monochrome(True)
    assert actors.monochrome

    with pytest.raises(ValueError):
        actors.set_to_monochrome(True, (255, 123, 33))

    actors.set_to_monochrome(True, (0.34, 0.44, 0.55))
    assert actors.monochrome_color == (0.34, 0.44, 0.55)


def test_to_vtk():
    """Test the to_vtk method."""
    file_path = r'./tests/assets/gridbased.hbjson'
    model = Model.from_hbjson(file_path)
    actors = Actors(model)
    vtk_actors = actors.to_vtk()
    assert isinstance(vtk_actors, list)
    check = [isinstance(actor, vtk.vtkActor) for actor in vtk_actors]
    assert check.count(True) == len(vtk_actors)


def test_bounds():
    """Test bounds."""
    file_path = r'./tests/assets/gridbased.hbjson'
    model = Model.from_hbjson(file_path)
    actors = Actors(model)
    bounds = actors.get_bounds()
    assert isinstance(bounds, list)
    check = [isinstance(point, Point3D) for point in bounds]
    assert check.count(True) == len(bounds)
