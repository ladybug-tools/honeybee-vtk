"""Unit test for actors module."""

import pytest
import vtk
from honeybee_vtk.actor import Actor
from honeybee_vtk.model import Model


file_path = r'tests/assets/gridbased.hbjson'


def test_class_initialization():
    """Test default properties of a Actors object."""
    with pytest.raises(TypeError):
        actors = Actor()

    actors = Model.from_hbjson(file_path).actors()
    for actor in actors:
        assert not actor.monochrome_color


def test_monochrome():
    """Test setting actors to monochrome colors."""
    actors = Model.from_hbjson(file_path).actors()
    with pytest.raises(ValueError):
        actors[0].get_monochrome((255, 123, 33))

    actors[0].get_monochrome((0.34, 0.44, 0.55))
    assert actors[0].monochrome_color == (0.34, 0.44, 0.55)


def test_to_vtk():
    """Test the to_vtk method."""
    actors = Model.from_hbjson(file_path).actors()
    for actor in actors:
        assert isinstance(actor.to_vtk(), vtk.vtkActor)
