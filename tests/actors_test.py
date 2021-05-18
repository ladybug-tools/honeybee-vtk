"""Unit test for actors module."""

import pytest
import vtk
from honeybee_vtk.actor import Actor
from honeybee_vtk.model import Model
from ladybug_geometry.geometry3d.pointvector import Point3D


def test_class_initialization():
    """Test default properties of a Actors object."""

    with pytest.raises(TypeError):
        actors = Actor()

    file_path = r'./tests/assets/gridbased.hbjson'
    model = Model.from_hbjson(file_path)
    actors = Actor.from_model(model)
    for actor in actors:
        assert not actor.monochrome_color


def test_monochrome():
    """Test setting actors to monochrome colors."""
    file_path = r'./tests/assets/gridbased.hbjson'
    model = Model.from_hbjson(file_path)
    actors = Actor.from_model(model)
    with pytest.raises(ValueError):
        actors[0].get_monochrome((255, 123, 33))

    actors[0].get_monochrome((0.34, 0.44, 0.55))
    assert actors[0].monochrome_color == (0.34, 0.44, 0.55)


def test_to_vtk():
    """Test the to_vtk method."""
    file_path = r'./tests/assets/gridbased.hbjson'
    model = Model.from_hbjson(file_path)
    actors = Actor.from_model(model)
    for actor in actors:
        assert isinstance(actor.to_vtk(), vtk.vtkActor)


def test_bounds():
    """Test bounds."""
    file_path = r'./tests/assets/gridbased.hbjson'
    model = Model.from_hbjson(file_path)
    actors = Actor.from_model(model)
    bounds = Actor.get_bounds(actors)
    assert isinstance(bounds, list)
    check = [isinstance(point, Point3D) for point in bounds]
    assert check.count(True) == len(bounds)
