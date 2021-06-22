"""Vtk legend parameters."""

import vtk
from ladybug.color import Colorset
from enum import Enum
from typing import Tuple
from ._helper import _validate_input


class LabelFormat (Enum):
    """Setting the type of the Label on a Legend.

    Types refers to two point decimal numbers, three point decimal numbers, and integers.
    """
    decimal_two = '%#6.2f'
    decimal_three = '%-#6.3f'
    default = '%-#6.3g'
    integer = '%4.3g'


class Orientation(Enum):
    """Orientation of a legend."""
    vertical = 'vertical'
    horizontal = 'horizontal'


class Colors(Enum):
    """Colors for a legend."""
    annual_comfort = Colorset.annual_comfort()
    benefit = Colorset.benefit()
    benefit_harm = Colorset.benefit_harm()
    black_to_white = Colorset.black_to_white()
    blue_green_red = Colorset.blue_green_red()
    cloud_cover = Colorset.cloud_cover()
    cold_sensation = Colorset.cold_sensation()
    ecotect = Colorset.ecotect()
    energy_balance = Colorset.energy_balance()
    energy_balance_storage = Colorset.energy_balance_storage()
    glare_study = Colorset.glare_study()
    harm = Colorset.harm()
    heat_sensation = Colorset.heat_sensation()
    multi_colored = Colorset.multi_colored()
    multicolored_2 = Colorset.multicolored_2()
    multicolored_3 = Colorset.multicolored_3()
    nuanced = Colorset.nuanced()
    openstudio_palette = Colorset.openstudio_palette()
    original = Colorset.original()
    peak_load_balance = Colorset.peak_load_balance()
    shade_benefit = Colorset.shade_benefit()
    shade_benefit_harm = Colorset.shade_benefit_harm()
    shade_harm = Colorset.shade_harm()
    shadow_study = Colorset.shadow_study()
    therm = Colorset.therm()
    thermal_comfort = Colorset.thermal_comfort()
    view_study = Colorset.view_study()


class Font:
    """Fonts for the legend.

        Args:
            color: A tuple of three integer values for R, G, and B. Defaults (0, 0, 0).
            size: An integer representing the size of fonts in points. Defaults to 30.
            bold: A boolean to specify whether the fonts should be made bold.
                Defaults to False.
        """

    def __init__(
            self, color: Tuple[float, float, float] = (0, 0, 0), size: int = 30,
            bold: bool = False) -> None:

        self.color = color
        self.size = size
        self.bold = bold

    @property
    def color(self) -> Tuple[float, float, float]:
        """Color of fonts in RGB decimal."""
        return self._color

    @color.setter
    def color(self, val) -> None:
        if not val:
            self._color = (0, 0, 0)
        elif isinstance(val, (tuple, list)) and _validate_input(val, int, 256) \
                and len(val) == 3:
            self._color = (val[0] / 255, val[1] / 255, val[1] / 255)
        else:
            raise ValueError(
                'Color accepts a tuple of a list of three integers for R, G, and B'
                f' values. Instead got {val}.'
            )

    @property
    def size(self) -> int:
        """Size of fonts."""
        return self._size

    @size.setter
    def size(self, val) -> None:
        if not val:
            self._size = 30
        elif isinstance(val, int):
            self._size = val
        else:
            raise ValueError(
                f'Size expects an integer value. Instead got {type(val).__name__}.'
            )

    @property
    def bold(self) -> bool:
        """To make font bold nor not."""
        return self._bold

    @bold.setter
    def bold(self, val) -> None:
        if not val:
            self._bold = False
        elif isinstance(val, bool):
            self._bold = val
        else:
            raise ValueError(
                f'Bold accepts boolean values only. Instead got {val}.'
            )

    def to_vtk(self) -> vtk.vtkTextProperty:
        """Create a vtk TextProperty object."""
        font = vtk.vtkTextProperty()
        font.SetColor(self._color[0], self._color[1], self._color[2])
        font.SetFontSize(self._size)
        if self._bold:
            font.BoldOn()
        return font

    def __repr__(self) -> Tuple[str]:
        return (
            f'Font color: {self._color} |'
            f' Font size: {self._size} |'
            f' Bold: {self._bold}'
        )


class LegendParameter:
    """Legend parameters for the vtk legend (scalarbar) object.

    A vtk legend has a number of colors, labels, and a title. Here, labels mean the
    numbers you see on a legend such as 0, 1, 2, 3, 4, 5 on a legend with max value of 5.

        Args:
            name: A text string representing the name of the legend object and the
                title of the legend. Default to "Legend".
            colors: A Colors object. Defaults to Ecotect colorset.
            range: A tuple of integers representing the minimum and maximum values of a
                legend. Defaults to (0, 100).
            show_legend: A boolean to set the visibility of a legend in Scene.
                Defaults to False.
            orientation: An Orientation object that sets the orientation of the legend in
                the scene. Defaults to horizontal orientation.
            position: A tuple of two decimal values. The values represent the percentage
                of viewport width and the percentage of viewport height. These
                percentages in decimal numbers will define the location of the start
                point of the legend. For example, a value of (0.0, 0.5) will place the
                start point of the legend at the left most side of the viewport and at
                the 50% height of the viewport. Default to (0.5, 0.1).
            width: A decimal number representing the percentage of viewport width that
                will be used to define the width of the legend. A value of 0.45 will
                make the width of legend equal to the 45% width of the viewport.
                Defaults to 0.45.
            height: A decimal number representing the percentage of viewport height that
                will be used to define the height of the legend. A value of 0.05 will
                make the height of legend equal to the 5% height of the viewport.
                Defaults to 0.05.
            number_of_colors: An integer representing the number of colors in a legend.
                Defaults to None.
            number_of_labels: An integer representing the number of text labels on a
                legend. Default to None.
            label_format: A LabelFormat object. Defaults to integer format.
            label_position: 0 or 1. The value of 0 would mean that the labels and the
                title would not precede the legend. The value of 1 would mean that the
                labels and the title would precede the legend. Defaults to 0.
            label_font: A Font object. Defaults to size 30 black fonts.
            title_font: A font object. Defaults to size 50 black bold fonts.
        """

    def __init__(
            self,
            name: str = 'Legend',
            colors: Colors = Colors.ecotect,
            range: Tuple[int, int] = (0, 100),
            show_legend: bool = False,
            orientation: Orientation = Orientation.horizontal,
            position: Tuple[float, float] = (0.5, 0.1),
            width: float = 0.45,
            height: float = 0.05,
            number_of_colors: int = None,
            number_of_labels: int = None,
            label_format: LabelFormat = LabelFormat.integer,
            label_position: int = 0,
            label_font: Font = Font(color=(0, 0, 0), size=30),
            title_font: Font = Font(color=(0, 0, 0), size=50, bold=True)) -> None:

        self.name = name
        self.colors = colors
        self.range = range
        self.show_legend = show_legend
        self.orientation = orientation
        self.position = position
        self.width = width
        self.height = height
        self.number_of_colors = number_of_colors
        self.number_of_labels = number_of_labels
        self.label_format = label_format
        self.label_position = label_position
        self.label_font = label_font
        self.title_font = title_font

    @property
    def name(self) -> str:
        """Name of the legend parameter object and the title of the legend."""
        return self._name

    @name.setter
    def name(self, val) -> None:
        if not val:
            self._name = 'Legend'
        elif isinstance(val, str):
            self._name = val
        else:
            raise ValueError(
                f'Name only accepts text. Instead got {type(val).__name__}.'
            )

    @property
    def colors(self) -> Colors:
        """Colors to be used in the legend."""
        return self._colors

    @colors.setter
    def colors(self, val) -> None:
        if not val:
            self._colors = Colors.ecotect
        elif isinstance(val, Colors):
            self._colors = val
        else:
            raise ValueError(
                f'A Colors object expected. Instead got {val}.'
            )

    @property
    def range(self) -> Tuple[float, float]:
        """A tuple with min and max values in the legend."""
        return self._range

    @range.setter
    def range(self, val) -> None:
        if not val:
            self._range = (0, 100)
        elif isinstance(val, (tuple, list)) and len(val) == 2:
            self._range = val
        else:
            raise ValueError(
                'Range takes a tuple or a list of integers.'
                f' Instead got {type(val).__name__}.'
            )

    @property
    def show_legend(self) -> bool:
        """Visibility of legend in the scene."""
        return self._show_legend

    @show_legend.setter
    def show_legend(self, val) -> None:
        if not val:
            self._show_legend = False
        elif isinstance(val, bool):
            self._show_legend = val
        else:
            raise ValueError(
                'Only a True or False value is accepted.'
            )

    @property
    def orientation(self) -> Orientation:
        """Orientation of a legend in the scene."""
        return self._orientation

    @orientation.setter
    def orientation(self, val) -> None:
        if not val:
            self._orientation = Orientation.horizontal
        elif isinstance(val, Orientation):
            self._orientation = val
        else:
            raise ValueError(
                'Orientation accepts either an Orientation object.'
                f' Instead got {type(val).__name__}.'
            )

    @property
    def position(self) -> Tuple[float, float]:
        return self._position

    @position.setter
    def position(self, val) -> None:
        if not val:
            self._position = (0.5, 0.1)
        elif isinstance(val, (tuple, list)) and _validate_input(val, float, 0.96) \
                and len(val) == 2:
            self._position = val
        else:
            raise ValueError(
                'Position accepts a tuple or a list of two decimal values up to 0.95'
                ' for both X and Y.'
            )

    @property
    def width(self) -> float:
        """Width of the legend as a percentage of viewport width."""
        return self._width

    @width.setter
    def width(self, val) -> None:
        if not val:
            self._width = 0.45
        elif val < 0.96:
            self._width = val
        else:
            raise ValueError(
                'Width accepts a decimal number up to 0.95.'
            )

    @property
    def height(self) -> float:
        """height of the legend as a percentage of viewport height."""
        return self._height

    @height.setter
    def height(self, val) -> None:
        if not val:
            self._height = 0.05
        elif val < 0.96:
            self._height = val
        else:
            raise ValueError(
                'Height accepts a decimal number up to 0.95.'
            )

    @property
    def number_of_colors(self) -> int:
        """Number of colors in the legend."""
        return self._number_of_colors

    @number_of_colors.setter
    def number_of_colors(self, val) -> None:
        if not val:
            self._number_of_colors = None
        elif isinstance(val, int) and 0 <= val <= len(self.colors.value):
            self._number_of_colors = val
        else:
            raise ValueError(
                'Number of colors must be an integer less than or equal to the number of'
                f'colors in the colors property. instead got {val}.'
            )

    @property
    def number_of_labels(self) -> int:
        """Number of text labels in the legend."""
        return self._number_of_labels

    @number_of_labels.setter
    def number_of_labels(self, val) -> None:
        if not val:
            self._number_of_labels = None
        elif isinstance(val, int) and 0 <= val <= len(self.colors.value):
            self._number_of_labels = val
        else:
            raise ValueError(
                'Number of labels must be an integer less than or equal to the number of'
                f'colors in the colors property. instead got {val}.'
            )

    @property
    def label_format(self) -> LabelFormat:
        """The format of legend labels."""
        return self._label_format

    @label_format.setter
    def label_format(self, val) -> None:
        if not val:
            self._label_format = LabelFormat.integer
        elif isinstance(val, LabelFormat):
            self._label_format = val
        else:
            raise ValueError(
                f'A LabelFormat object expected. Instead got {type(val).__name__}'
            )

    @property
    def label_position(self) -> int:
        """The position of labels and the legend title on a legend.

        The value of 0 would mean that the labels and the title would not preced the
        legend. The value of 1 would mean that the labels and the title would precede
        the legend.
        """
        return self._label_position

    @label_position.setter
    def label_position(self, val):
        if not val:
            self._label_position = 0
        elif isinstance(val, int) and val in [0, 1]:
            self._label_position = val
        else:
            raise ValueError(
                f'Label position only accepts 0 or 1 as a value. Instead got {val}.'
            )

    @property
    def label_font(self) -> Font:
        """Font for the legend labels."""
        return self._label_font

    @label_font.setter
    def label_font(self, val) -> None:
        if not val:
            self._label_font = Font(color=(0, 0, 0), size=30)
        elif isinstance(val, Font):
            self._label_font = val
        else:
            raise ValueError(
                f'Label font expects a Font object. Instead got {type(val).__name__}.'
            )

    @property
    def title_font(self) -> Font:
        """Font for the legend title."""
        return self._title_font

    @title_font.setter
    def title_font(self, val) -> None:
        if not val:
            self._title_font = Font(color=(0, 0, 0), size=30, bold=True)
        elif isinstance(val, Font):
            self._title_font = val
        else:
            raise ValueError(
                f'Title font expects a Font object. Instead got {type(val).__name__}.'
            )

    def get_lookuptable(self) -> vtk.vtkLookupTable:
        """Get a vtk lookuptable."""
        minimum, maximum = self._range
        color_values = self._colors.value
        lut = vtk.vtkLookupTable()
        lut.SetRange(minimum, maximum)
        lut.SetRampToLinear()
        lut.SetValueRange(minimum, maximum)
        lut.SetHueRange(0, 0)
        lut.SetSaturationRange(0, 0)

        lut.SetNumberOfTableValues(len(color_values))
        for count, color in enumerate(color_values):
            lut.SetTableValue(
                count, color.r / 255, color.g / 255, color.b / 255, color.a / 255
            )
        lut.Build()
        lut.SetNanColor(1, 0, 0, 1)
        return lut

    def get_scalarbar(self) -> vtk.vtkScalarBarActor:
        """Get a vtk scalar bar (legend)."""

        color_range = self.get_lookuptable()

        scalar_bar = vtk.vtkScalarBarActor()
        scalar_bar.SetLookupTable(color_range)
        scalar_bar.SetTitle(self._name)
        scalar_bar.SetPosition(self._position)
        scalar_bar.SetWidth(self._width)
        scalar_bar.SetHeight(self._height)
        # The following allows the change in font size for the text labels on the legend
        scalar_bar.SetUnconstrainedFontSize(True)

        if self._orientation == Orientation.horizontal:
            scalar_bar.SetOrientationToHorizontal()
        else:
            scalar_bar.SetOrientationToVertical()

        if self._number_of_colors:
            scalar_bar.SetMaximumNumberOfColors(self._number_of_colors)
        if self._number_of_labels:
            scalar_bar.SetNumberOfLabels(self._number_of_labels)

        # setting the type of labels. Such as integers, decimals, etc.
        scalar_bar.SetLabelFormat(self._label_format.value)

        # Setting whether the labels and title should precede the legend
        scalar_bar.SetTextPosition(self._label_position)

        scalar_bar.SetLabelTextProperty(self._label_font.to_vtk())
        scalar_bar.SetTitleTextProperty(self._title_font.to_vtk())

        return scalar_bar

    def __repr__(self) -> Tuple[str]:
        return (
            f'Legend name: {self._name} |'
            f' Legend visibility: {self._show_legend} |'
            f' Legend color scheme: {self._colors.name} |'
            f' Legend range: {self._range} |'
            f' Legend visibility: {self._show_legend} |'
            f' Legend orientation: {self._orientation} |'
            f' Legend position: {self._position} |'
            f' Legend width: {self._width} |'
            f' Legend height: {self._height} |'
            f' Number of colors in legend: {self._number_of_colors} |'
            f' Number of lables in legend: {self._number_of_labels} |'
            f' Type of label: {self._label_format} |'
            f' Position of label: {self._label_position} |'
            f' Font of label: {self._label_font} |'
            f' Font of title: {self._title_font}'
        )
