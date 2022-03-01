"""Data json schema and validation for the config file."""

from __future__ import annotations


from typing import List, Union
from pydantic import BaseModel, validator, Field, constr, conint
from pydantic.types import confloat, conlist
from .types import DataSetNames
from .legend_parameter import ColorSets, DecimalCount, Orientation


class InputFile(BaseModel):
    """Config for the input file to be consumed by the config command."""
    paths: List[str] = Field(
        description='Paths to the result folders.')

    identifiers: List[str] = Field(
        description='Identifiers for the simulation data that will be mounted on the'
        ' model. The length of this list must match the length of paths.')

    units: List[str] = Field(
        description='Units for the simulation data that will be mounted on the'
        ' model. The length of this list must match the length of paths.')

    @validator('identifiers', 'units')
    def check_length(cls, v, values):
        """Check that the length of identifiers and units match the length of paths."""
        if len(values['paths']) != len(v):
            raise ValueError('The length of paths, identifiers, and units must match.')
        return v


class Autocalculate(BaseModel):

    type: constr(regex='^Autocalculate$') = 'Autocalculate'


class TextConfig(BaseModel):
    """Config for the text to be used in a legend.

    This object applies to text for legend title and legend labels as well.
    """

    class Config:
        validate_all = True
        validate_assignment = True

    color: List[conint(ge=0, le=255)] = Field(
        [0, 0, 0],
        description='An array of three integer values representing R, G, and B values'
        ' for the color of text. Values from 0 to 255 are accepted.'
    )

    size: conint(ge=0) = Field(
        0,
        description='Text size in points.'
    )

    bold: bool = Field(
        False,
        description='Boolean value to indicate whether to make the text bold or not.'
    )


class LegendConfig(BaseModel):
    """Config for the legend to be created from a dataset."""
    class Config:
        validate_all = True
        validate_assignment = True

    color_set: ColorSets = Field(
        ColorSets.ecotect,
        description='Color set to be used on data and legend. Currently, this field'
        ' only uses Ladybug color sets. Defaults to using ecotect colorset.'
    )

    min: Union[Autocalculate, float] = Field(
        Autocalculate(),
        description='Minimum value for the legend. Also known as the lower end of the'
        ' legend. If min and max values are not specified, autocalculated min and max'
        ' values will be used from data.'
    )

    max: Union[Autocalculate, float] = Field(
        Autocalculate(),
        description='Maximum value for the legend. Also known as the higher end of the'
        ' legend. If min and max values are not specified, autocalculated min and max'
        ' values will be used from data.'
    )

    hide_legend: bool = Field(
        False,
        description='A bool value to indicate whether to show legend in the exported'
        ' images or not.'
    )

    orientation: Orientation = Field(
        Orientation.vertical,
        description='Choose between horizontal and vertical orientation of legend.'
    )

    width: confloat(ge=0.05, le=0.95) = Field(
        0.05,
        description=' A decimal number representing the fraction of viewport width'
        ' that will be used to define the width of the legend.'
    )

    height: confloat(ge=0.05, le=0.95) = Field(
        0.45,
        description='A decimal number representing the fraction of viewport height'
        'that will be used to define the height of the legend.'
    )

    position: conlist(confloat(ge=0.05, le=0.95), min_items=2, max_items=2) = Field(
        [0.9, 0.5],
        description='A tuple of two decimal values. The values represent the fraction'
        ' of viewport width and the fraction of viewport height.'
    )

    color_count: Union[Autocalculate, int] = Field(
        Autocalculate(),
        description='An integer representing the number of colors in a legend. If not'
        ' specified, it defaults to the number of colors in a Ladybug color set.'
    )

    label_count: Union[Autocalculate, int] = Field(
        Autocalculate(),
        description='An integer representing the number of text labels on a legend.'
        ' Label count will have to be less than or equal to color count. It defaults'
        ' to vtk scalarbar default setting.'
    )

    decimal_count: DecimalCount = Field(
        DecimalCount.default,
        description='Controlling the number of decimals on each label of the legend.'
        'Accepted values are "default", "integer", "decimal_two", and "decimal_three".'
        'Defaults to VTKs default settings.'
    )

    preceding_labels: bool = Field(
        False,
        description='Boolean value to decide whether the legend title and the'
        ' legend labels will precede the legend or not.'
    )

    label_parameters: TextConfig = Field(
        TextConfig(),
        description='Text parameters for the labels on the legend.'
    )

    title_parameters: TextConfig = Field(
        TextConfig(bold=True),
        description='Text parameters for the title of the legend.'
    )


class DataConfig(BaseModel):
    """data-config for simulation results you'd like to load on a honeybee-vtk model."""

    identifier: str = Field(
        description='identifier to be given to data. Example, "Daylight-Factor".'
        ' This identifier needs to be unique in each of the DataConfig objects'
        ' one introduces using a config file. Having multiple DataConfig objects with'
        ' same modifier will raise an error.'
    )

    object_type: DataSetNames = Field(
        description='The name of the model object on which you would like to map this'
        ' data.'
    )

    unit: str = Field(
        description=' The unit of the data being loaded.'
    )

    path: str = Field(
        description='Valid path to the folder with result files and the json file that'
        ' catalogues the results.'
    )

    hide: bool = Field(
        False,
        description='Boolean value to indicate if this data should be visible in the'
        ' exported images or not.'
    )

    legend_parameters: LegendConfig = Field(
        LegendConfig(),
        description='Legend parameters to create legend out of the this dataset.'
    )

    @validator('identifier')
    def check_space(cls, v: str) -> str:
        """Check that identifier does not contain spaces.

        This check is needed to make the identifier compliant with Radiance.
        """
        if ' ' in v:
            raise ValueError('Identifier cannot have a blank space.')
        return v

    @validator('legend_parameters')
    def check_pos_against_width_height(cls, v: LegendConfig, values) -> LegendConfig:
        id = values['identifier']
        if v.width >= 0.5 and v.position[0] >= 0.5 and v.width > v.position[0]:
            raise ValueError(
                f'Width of legend {id}, {v.width}'
                f' cannot be greater than the position of legend in X direction'
                f' {v.position[0]}.'
                ' Either update the position in X direction or update the'
                ' width of the legend. \n'
            )
        if v.height >= 0.5 and v.position[1] >= 0.5 and v.height > v.position[1]:
            raise ValueError(
                f'Height of legend {id}, {v.height}'
                f' cannot be greater than the position of legend in Y direction'
                f' {v.position[1]}.'
                ' Either update the position in Y direction or update the'
                ' height of the legend. \n'
            )
        return v


class Config(BaseModel):
    """Config for simulation results you'd like to load on a honeybee-vtk model."""

    data: List[DataConfig] = Field(
        description='List of data-config objects that define the data to be loaded on'
        ' the model.'
    )
