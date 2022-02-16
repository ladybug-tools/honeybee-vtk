"""Honeybee-vtk TextActor object."""

import vtk
from typing import Tuple


class TextActor:
    def __init__(self, text: str, hight: int = 15, color: Tuple[int, int, int] = (0, 0, 0),
                 position: Tuple[float, float] = (0.5, 0.0), bold: bool = False) -> None:
        self.text = text
        self.hight = hight
        self.color = color
        self.position = position
        self.bold = bold

    def to_vtk(self) -> vtk.vtkTextActor:
        """Create a vtk text actor."""

        text_actor = vtk.vtkTextActor()
        text_actor.SetInput(self.text)
        text_actor.GetTextProperty().SetFontFamilyToArial()
        text_actor.GetTextProperty().SetFontSize(self.hight)
        text_actor.GetTextProperty().SetColor(self.color)
        text_actor.GetPositionCoordinate().SetCoordinateSystemToNormalizedDisplay()
        text_actor.SetPosition(self.position[0], self.position[1])
        if self.bold:
            text_actor.GetTextProperty().BoldOn()

        return text_actor
