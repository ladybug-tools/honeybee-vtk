"""Unit tests for the legend_parameter module."""

import pytest
import vtk
from honeybee_vtk.legend_parameter import Font, LabelFormat, LegendParameter
from honeybee_vtk.legend_parameter import Colors, Orientation
from honeybee_vtk._helper import _validate_input


def test_font_initialization():
    """Testing initialization of a Font object."""

    font = Font()

    assert font.color == (0, 0, 0)
    assert font.size == (30)
    assert not font.bold
    assert isinstance(font.to_vtk(), vtk.vtkTextProperty)


def test_font_errors():
    """Testing if correct exceptions are raised."""

    font = Font()

    with pytest.raises(ValueError):
        font.color = 0.1, 0.1, 0.1

    with pytest.raises(ValueError):
        font.size = 4.5

    with pytest.raises(ValueError):
        font.bold = 2

    font.color = (54, 54, 54)
    assert _validate_input(font.color, float)


def test_legend_parameter_initialization():
    """Testing initialization of a legend_parameter object."""

    lp = LegendParameter()

    assert lp.name == 'Legend'
    assert lp.colors == Colors.ecotect
    assert lp.range == (0, 100)
    assert not lp.show_legend
    assert lp.orientation == Orientation.horizontal
    assert lp.position == (0.5, 0.1)
    assert lp.width == 0.45
    assert lp.height == 0.05
    assert not lp.number_of_colors
    assert not lp.number_of_labels
    assert lp.label_format == LabelFormat.integer
    assert lp.label_position == 0
    assert isinstance(lp.label_font, Font)
    assert isinstance(lp.title_font, Font)
    assert isinstance(lp.get_lookuptable(), vtk.vtkLookupTable)
    assert isinstance(lp.get_scalarbar(), vtk.vtkScalarBarActor)


def test_legend_parameter_errors():
    """Test if correct exceptions are raised."""

    lp = LegendParameter()

    with pytest.raises(ValueError):
        lp.name = 2
    with pytest.raises(ValueError):
        lp.range = (0.1, 0.5, 3)
    with pytest.raises(ValueError):
        lp.show_legend = 3
    with pytest.raises(ValueError):
        lp.orientation = 90
    with pytest.raises(ValueError):
        lp.position = (2, 3)
    with pytest.raises(ValueError):
        lp.width = 0.96
    with pytest.raises(ValueError):
        lp.height = 0.96
    with pytest.raises(ValueError):
        lp.number_of_labels = 25
    with pytest.raises(ValueError):
        lp.number_of_colors = 25
    with pytest.raises(ValueError):
        lp.label_format = int
    with pytest.raises(ValueError):
        lp.label_position = 4
    with pytest.raises(ValueError):
        lp.label_font = 'Arial'
    with pytest.raises(ValueError):
        lp.title_font = 'Italic'
