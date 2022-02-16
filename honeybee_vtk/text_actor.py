"""Honeybee-vtk TextActor object."""

import vtk
from typing import Tuple


class TextActor:

    """Use this object to create a vtk text actor. 

    This text actor can be used to add text to a vtk scene.

    Args:
        text: Text to be added to the Scene.
        height: Text height in pixels. Default is 15.
        color: Text color as a tuple of RGB values. Defaults to (0,0,0) which will give
            the text black color.
        position: The text position of the text in the image as a tuple of (x, y).
            The setting is applied at the lower left point of the text. 
            (0,0) will give you the lower left corner of the image.
            (1,1) will give you the upper right corner of the image.
            Defaults to (0.5, 0.0) which will put the text at the bottom center of 
            the image.
        bold: Boolean to decide whether to make the text bold. Defaults to False.
    """

    def __init__(self, text: str, height: int = 15, color: Tuple[int, int, int] = (0, 0, 0),
                 position: Tuple[float, float] = (0.5, 0.0), bold: bool = False) -> None:
        self.text = text
        self.height = height
        self.color = color
        self.position = position
        self.bold = bold

    @property
    def text(self) -> str:
        """Get the text."""
        return self._text

    @text.setter
    def text(self, text: str) -> None:
        """Set the text."""
        self._text = text

    @property
    def height(self) -> int:
        """Get the text height."""
        return self._height

    @height.setter
    def height(self, height: int) -> None:
        """Set the text height."""
        self._height = height

    @property
    def color(self) -> Tuple[int, int, int]:
        """Get the text color."""
        return self._color

    @color.setter
    def color(self, color: Tuple[int, int, int]) -> None:
        """Set the text color."""
        self._color = color

    @property
    def position(self) -> Tuple[float, float]:
        """Get the text position."""
        return self._position

    @position.setter
    def position(self, position: Tuple[float, float]) -> None:
        """Set the text position."""
        self._position = position

    def __repr__(self) -> str:
        """Representation of the TextActor."""
        return f"TextActor: {self.text}"

    def to_vtk(self) -> vtk.vtkTextActor:
        """Create a vtk text actor."""

        text_actor = vtk.vtkTextActor()
        text_actor.SetInput(self.text)
        text_actor.GetTextProperty().SetFontFamilyToArial()
        text_actor.GetTextProperty().SetFontSize(self.height)
        text_actor.GetTextProperty().SetColor(self.color)
        text_actor.GetPositionCoordinate().SetCoordinateSystemToNormalizedDisplay()
        text_actor.SetPosition(self.position[0], self.position[1])
        if self.bold:
            text_actor.GetTextProperty().BoldOn()

        return text_actor
