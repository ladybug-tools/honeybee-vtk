"""Vtk legend parameters."""

import vtk
from ladybug.color import Colorset, Color
from enum import Enum
from typing import Tuple, Union, List
from ._helper import _validate_input


class DecimalCount (Enum):
    """Controlling the number of decimals on each label of the legend."""
    decimal_two = 'decimal_two'
    decimal_three = 'decimal_three'
    default = 'default'
    integer = 'integer'


decimal_count = {'decimal_two': '%#6.2f', 'decimal_three': '%-#6.3f',
                 'default': '%-#6.3g', 'integer': '%4.3g'}


decimal_count = {'decimal_two': '%#6.2f', 'decimal_three': '%-#6.3f',
                 'default': '%-#6.3g', 'integer': '%4.3g'}


class Orientation(Enum):
    """Orientation of a legend."""
    vertical = 'vertical'
    horizontal = 'horizontal'


class ColorSets(Enum):
    """Colors for a legend."""
    annual_comfort = 'annual_comfort'
    benefit = 'benefit'
    benefit_harm = 'benefit_harm'
    black_to_white = 'black_to_white'
    blue_green_red = 'blue_green_red'
    cloud_cover = 'cloud_cover'
    cold_sensation = 'cold_sensation'
    ecotect = 'ecotect'
    energy_balance = 'energy_balance'
    energy_balance_storage = 'energy_balance_storage'
    glare_study = 'glare_study'
    harm = 'harm'
    heat_sensation = 'heat_sensation'
    multi_colored = 'multi_colored'
    multicolored_2 = 'multicolored_2'
    multicolored_3 = 'multicolored_3'
    nuanced = 'nuanced'
    openstudio_palette = 'openstudio_palette'
    original = 'original'
    peak_load_balance = 'peak_load_balance'
    shade_benefit = 'shade_benefit'
    shade_benefit_harm = 'shade_benefit_harm'
    shade_harm = 'shade_harm'
    shadow_study = 'shadow_study'
    therm = 'therm'
    thermal_comfort = 'thermal_comfort'
    view_study = 'view_study'


color_set = {
    'annual_comfort': Colorset.annual_comfort(),
    'benefit': Colorset.benefit(),
    'benefit_harm': Colorset.benefit_harm(),
    'black_to_white': Colorset.black_to_white(),
    'blue_green_red': Colorset.blue_green_red(),
    'cloud_cover': Colorset.cloud_cover(),
    'cold_sensation': Colorset.cold_sensation(),
    'ecotect': Colorset.ecotect(),
    'energy_balance': Colorset.energy_balance(),
    'energy_balance_storage': Colorset.energy_balance_storage(),
    'glare_study': Colorset.glare_study(),
    'harm': Colorset.harm(),
    'heat_sensation': Colorset.heat_sensation(),
    'multi_colored': Colorset.multi_colored(),
    'multicolored_2': Colorset.multicolored_2(),
    'multicolored_3': Colorset.multicolored_3(),
    'nuanced': Colorset.nuanced(),
    'openstudio_palette': Colorset.openstudio_palette(),
    'original': Colorset.original(),
    'peak_load_balance': Colorset.peak_load_balance(),
    'shade_benefit': Colorset.shade_benefit(),
    'shade_benefit_harm': Colorset.shade_benefit_harm(),
    'shade_harm': Colorset.shade_harm(),
    'shadow_study': Colorset.shadow_study(),
    'therm': Colorset.therm(),
    'thermal_comfort': Colorset.thermal_comfort(),
    'view_study': Colorset.view_study()
}


class Text:
    """Text parameters for the legend.

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
        elif isinstance(val, (tuple, list)) and _validate_input(val, [int], 256) \
                and len(val) == 3:
            self._color = (val[0] / 255, val[1] / 255, val[2] / 255)
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
            self._size = 0
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
            unit: A text string representing the unit of the data that the legend
                represents. Examples are 'celsius', 'kwn/m2', etc.
            colorset: A ColorSet object. Defaults to Ecotect colorset.
            reverse_colorset: A boolean to specify whether the colorset should be
                reversed. Defaults to False.
            hide_legend: A boolean to set the visibility of a legend in Scene.
                Defaults to False.
            orientation: An Orientation object that sets the orientation of the legend in
                the scene. Defaults to horizontal orientation.
            position: A tuple of two decimal values. The values represent the fraction
                of viewport width and the fraction of viewport height. These
                fractions in decimal numbers will define the location of the start
                point of the legend. For example, a value of (0.0, 0.5) will place the
                start point of the legend at the left most side of the viewport and at
                the 50% height of the viewport. Defaults to (0.5, 0.1).
            width: A decimal number representing the fraction of viewport width that
                will be used to define the width of the legend. A value of 0.45 will
                make the width of legend equal to the 45% width of the viewport.
                Defaults to 0.45.
            height: A decimal number representing the fraction of viewport height that
                will be used to define the height of the legend. A value of 0.05 will
                make the height of legend equal to the 5% height of the viewport.
                Defaults to 0.05.
            color_count: An integer representing the number of colors in a legend.
                Defaults to None which will use all the colors in the colors property.
            label_count: An integer representing the number of text labels on a
                legend. Default to None which will use vtk legend's default setting.
            decimal_count: A DecimalCount object that specifies the number of decimals
                on each label of the legend. Defaults to the type of data. For data
                with integer values this will default to integer. Similarly, for data
                with decimal values, this will default to decimal point numbers.
            preceding_labels: A boolean value to indicate whether the title and the
                labels should precede the legend or not. Defaults to False.
            label_parameters: A Text object. Defaults to size 30 black text.
            title_parameters: A Text object. Defaults to size 50 black bold text.
            min: A number that will be set as the lower bound of the legend.
                Defaults to None.
            min: A number that will be set as the upper bound of the legend.
                Defaults to None.
            auto_range: A tuple of minimum and maximum values for legend. This is
                auto set when Data is loaded on a model. Use min and max arguments to
                customize this auto calculated range.
        """

    def __init__(
            self,
            name: str = 'Legend',
            unit: str = '',
            colorset: ColorSets = ColorSets.ecotect,
            reverse_colorset: bool = False,
            hide_legend: bool = False,
            orientation: Orientation = Orientation.horizontal,
            position: Tuple[float, float] = (0.5, 0.1),
            width: float = 0.45,
            height: float = 0.05,
            color_count: int = None,
            label_count: int = None,
            decimal_count: DecimalCount = DecimalCount.default,
            preceding_labels: bool = False,
            label_parameters: Text = Text(color=(0, 0, 0), size=0),
            title_parameters: Text = Text(color=(0, 0, 0), size=0, bold=True),
            min: Union[float, int] = None,
            max: Union[float, int] = None,
            auto_range: Tuple[float, float] = None) -> None:

        self.name = name
        self.unit = unit
        self.colorset = colorset
        self.reverse_colorset = reverse_colorset
        self.hide_legend = hide_legend
        self.orientation = orientation
        self.position = position
        self.width = width
        self.height = height
        self.color_count = color_count
        self.label_count = label_count
        self.decimal_count = decimal_count
        self.preceding_labels = preceding_labels
        self.label_parameters = label_parameters
        self.title_parameters = title_parameters
        self.min = min
        self.max = max
        self.auto_range = auto_range
        self._colors = ()

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
    def unit(self) -> str:
        """Unit for the data that the legend represents."""
        return self._unit

    @unit.setter
    def unit(self, val) -> None:
        if not val:
            self._unit = ''
        elif isinstance(val, str):
            self._unit = val
        else:
            raise ValueError(
                f'Unit only accepts text. Instead got {type(val).__name__}.'
            )

    @property
    def colorset(self) -> ColorSets:
        """Colors to be used in the legend."""
        return self._colorset

    @colorset.setter
    def colorset(self, val) -> None:
        if not val:
            self._colorset = ColorSets.ecotect
        elif isinstance(val, ColorSets):
            self._colorset = val
        else:
            raise ValueError(
                f'A ColorSet objects expected. Instead got {val}.'
            )

    @property
    def reverse_colorset(self) -> bool:
        """A boolean to specify whether the colorset should be reversed."""
        return self._reverse_colorset

    @reverse_colorset.setter
    def reverse_colorset(self, val) -> None:
        if not val:
            self._reverse_colorset = False
        elif isinstance(val, bool):
            self._reverse_colorset = val
        else:
            raise ValueError(
                f'A boolean value expected. Instead got {val}.'
            )

    @property
    def hide_legend(self) -> bool:
        """Visibility of legend in the scene."""
        return self._hide_legend

    @hide_legend.setter
    def hide_legend(self, val) -> None:
        if not val:
            self._hide_legend = False
        elif isinstance(val, bool):
            self._hide_legend = val
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
        elif isinstance(val, (tuple, list)) and _validate_input(val, [float], 0.96) \
                and len(val) == 2:
            self._position = val
        else:
            raise ValueError(
                'Position accepts a tuple or a list of two decimal values up to 0.95'
                ' for both X and Y.'
            )

    @property
    def width(self) -> float:
        """Width of the legend as a fraction of viewport width."""
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
        """height of the legend as a fraction of viewport height."""
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
    def color_count(self) -> int:
        """Number of colors in the legend."""
        return self._color_count

    @color_count.setter
    def color_count(self, val) -> None:
        if not val:
            self._color_count = None
        elif isinstance(val, int) and 0 <= val <= len(self.colorset.value):
            self._color_count = val
        else:
            raise ValueError(
                'Color count must be a number less than or equal to the number of'
                f' colors in the colors property, which is {len(self.colorset.value)}.'
                f' Instead got {val}.'
            )

    @property
    def label_count(self) -> int:
        """Number of text labels in the legend."""
        return self._label_count

    @label_count.setter
    def label_count(self, val) -> None:
        if not val:
            self._label_count = None
        elif not self._color_count:
            if isinstance(val, int) and 0 <= val <= len(self.colorset.value):
                self._label_count = val
            else:
                raise ValueError(
                    'Label count must be a number less than or equal to the number of'
                    f' colors {len(self.colorset.value)}. Instead got {val}.'
                )
        elif self._color_count:
            if isinstance(val, int) and 0 <= val <= self._color_count:
                self._label_count = val
            else:
                raise ValueError(
                    'Label count must be a number less than or equal to'
                    f' color count, which is {self._color_count}. Instead got {val}.'
                )

    @property
    def decimal_count(self) -> DecimalCount:
        """The format of legend labels."""
        return self._decimal_count

    @decimal_count.setter
    def decimal_count(self, val) -> None:
        if not val:
            self._decimal_count = DecimalCount.default
        elif isinstance(val, DecimalCount):
            self._decimal_count = val
        else:
            raise ValueError(
                f'A DecimalCount object expected. Instead got {type(val).__name__}'
            )

    @property
    def preceding_labels(self) -> int:
        """Boolean to indicate whether the title and the labels should precede the legend
        or not."""
        return self._preceding_labels

    @preceding_labels.setter
    def preceding_labels(self, val):
        if not val:
            self._preceding_labels = False
        elif isinstance(val, bool):
            self._preceding_labels = val
        else:
            raise ValueError(
                f'Label position only accepts boolean values. Instead got {val}.'
            )

    @property
    def label_parameters(self) -> Text:
        """Font for the legend labels."""
        return self._label_parameters

    @label_parameters.setter
    def label_parameters(self, val) -> None:
        if not val:
            self._label_parameters = Text()
        elif isinstance(val, Text):
            self._label_parameters = val
        else:
            raise ValueError(
                f'Label font expects a Font object. Instead got {type(val).__name__}.'
            )

    @property
    def title_parameters(self) -> Text:
        """Font for the legend title."""
        return self._title_parameters

    @title_parameters.setter
    def title_parameters(self, val) -> None:
        if not val:
            self._title_parameters = Text(bold=True)
        elif isinstance(val, Text):
            self._title_parameters = val
        else:
            raise ValueError(
                f'Title font expects a Font object. Instead got {type(val).__name__}.'
            )

    @property
    def min(self):
        return self._min

    @min.setter
    def min(self, val):
        if val is None:
            self._min = None
        elif isinstance(val, (int, float)):
            self._min = val
        else:
            raise ValueError(
                f'Min must be a number. Instead got {val}.'
            )

    @property
    def max(self):
        return self._max

    @max.setter
    def max(self, val):
        if val is None:
            self._max = None
        elif isinstance(val, (int, float)):
            self._max = val
        else:
            raise ValueError(
                f'Max must be a number. Instead got {val}.'
            )

    @property
    def range(self) -> Tuple[float, float]:
        if self._min is None and self._max is None:
            return self.auto_range

        elif self._min and self._max is None:
            if self._min < self.auto_range[1]:
                return (self._min, self.auto_range[1])
            else:
                raise ValueError(
                    f'In {self._name},'
                    f' min value {self._min} must be less than auto-calculated'
                    f' max value {self.auto_range[1]}. Either update min value or'
                    ' provide a max value.'
                )

        elif self._min is None and self._max:
            if self._max > self.auto_range[0]:
                return (self.auto_range[0], self._max)
            else:
                raise ValueError(
                    f'In {self._name},'
                    f' max value {self._max} must be greater than auto-calculated'
                    f' max value {self.auto_range[1]}. Either update max value or'
                    ' provide a min value.'
                )

        elif isinstance(self._min, (int, float)) and isinstance(self._max, (int, float)):
            if self._min < self._max:
                return (self._min, self._max)
            else:
                raise ValueError(
                    f'In {self._name},'
                    f' make sure max value {self._max} is greater than the min'
                    f' value {self._min}.'
                )

    def _assign_colors(self, val: List[Color]) -> None:
        """Assign colors instead of a colorset.

        This private method is currently used in to_grid_images method of vtk Model.
        """
        colors = tuple(val)
        self._colors = colors
        self._color_count = len(colors)
        self.label_count = self._color_count

    def _to_dict(self) -> dict:
        """Get the legend parameters as a dictionary object.

        This method is only used in the 'translate' command.
        """
        return {
            'name': self._name,
            'unit': self._unit,
            'colors': self._colorset.value,
            'reverse_colorset': self._reverse_colorset,
            'hide_legend': self._hide_legend,
            'color_count': self._color_count,
            'label_count': self._label_count,
            'min': self._min,
            'max': self._max,
            'range': self.range
        }

    def get_lookuptable(self) -> vtk.vtkLookupTable:
        """Get a vtk lookuptable."""
        minimum, maximum = self.range
        if not self._colors:
            color_values = color_set[self._colorset.value]
            if self._reverse_colorset:
                color_values = list(color_values)
                color_values.reverse()
        else:
            color_values = self._colors

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

        lookup_table = self.get_lookuptable()

        scalar_bar = vtk.vtkScalarBarActor()
        scalar_bar.SetLookupTable(lookup_table)

        if self._unit:
            scalar_bar.SetTitle(f'{self._name} [{self._unit}]')
        else:
            scalar_bar.SetTitle(self._name)

        scalar_bar.SetTextPad(2)
        scalar_bar.SetPosition(self._position)
        scalar_bar.SetWidth(self._width)
        scalar_bar.SetHeight(self._height)
        # The following allows the change in font size for the text labels on the legend
        scalar_bar.SetUnconstrainedFontSize(True)

        if self._orientation == Orientation.horizontal:
            scalar_bar.SetOrientationToHorizontal()
        else:
            scalar_bar.SetOrientationToVertical()

        if self._color_count:
            scalar_bar.SetMaximumNumberOfColors(self._color_count)
        if self._label_count:
            scalar_bar.SetNumberOfLabels(self._label_count)

        # setting the type of labels. Such as integers, decimals, etc.
        scalar_bar.SetLabelFormat(decimal_count[self._decimal_count.value])

        # Setting whether the labels and title should precede the legend
        scalar_bar.SetTextPosition(self._preceding_labels)

        self._label_parameters.size = round(self._title_parameters.size * 0.8)
        scalar_bar.SetLabelTextProperty(self._label_parameters.to_vtk())
        scalar_bar.SetTitleTextProperty(self._title_parameters.to_vtk())

        return scalar_bar

    def __repr__(self) -> Tuple[str]:
        return (
            f'Legend name: {self._name} |'
            f' Legend title: {self._unit} |'
            f' Legend visibility: {self._hide_legend} |'
            f' Legend color scheme: {self._colorset.name} |'
            f' Legend orientation: {self._orientation} |'
            f' Legend position: {self._position} |'
            f' Legend width: {self._width} |'
            f' Legend height: {self._height} |'
            f' Number of colors in legend: {self._color_count} |'
            f' Number of lables in legend: {self._label_count} |'
            f' Type of label: {self._decimal_count} |'
            f' Position of label: {self._preceding_labels} |'
            f' Font of label: {self._label_parameters} |'
            f' Font of title: {self._title_parameters} |'
            f' Legend min: {self._min} |'
            f' Legend max: {self._max} |'
            f' Legend range: {self.range} |'
        )
