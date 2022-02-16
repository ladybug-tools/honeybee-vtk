"""Unit test for the TextActor class."""

import vtk
from honeybee_vtk.text_actor import TextActor


def test_object_initialization():
    """Test the object initialization."""
    text_actor = TextActor('Yeah')
    assert text_actor.text == 'Yeah'
    assert text_actor.height == 15
    assert text_actor.color == (0, 0, 0)
    assert text_actor.position == (0.5, 0.0)
    assert not text_actor.bold


def test_to_vtk_translation():
    """Test the to_vtk method."""
    text_actor = TextActor('Yeah')
    vtk_text_actor = text_actor.to_vtk()
    assert isinstance(vtk_text_actor, vtk.vtkTextActor)
    assert vtk_text_actor.GetInput() == 'Yeah'
    assert vtk_text_actor.GetTextProperty().GetFontFamily() == 0
    assert vtk_text_actor.GetTextProperty().GetFontSize() == 15
    assert vtk_text_actor.GetTextProperty().GetColor() == (0, 0, 0)
    assert vtk_text_actor.GetPosition() == (0.5, 0.0)
    assert not vtk_text_actor.GetTextProperty().GetBold()
