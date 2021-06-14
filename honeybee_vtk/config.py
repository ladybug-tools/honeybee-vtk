"""Data json schema and validation."""


from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, fields, validator, Field
from pydantic.errors import DecimalError
from .types import model_dataset_names
from .legend_parameter import Colors, Orientation, LabelFormat, Font


class FontConfig(BaseModel):
    pass


class LegendConfig(BaseModel):
    """Config for legend to be created from a dataset."""

    name: Optional[str] = Field(
        description='Name for the legend. This will also become the title of the legend.'
    )

    colors: Optional[str] = Field(
        description='Color scheme for the legend.'
    )

    range: Optional[List[int]] = Field(
        description='A list of minimum and maximum values for the legend.'
    )

    show_legend: Optional[bool] = Field(
        description='A bool value to indicate whether to show legend in the exported'
        ' images or not.'
    )

    orientation: Optional[str] = Field(
        description='Choose between horizontal and vertical orientation.'
    )

    position: Optional[List[float]] = Field(
        description='A tuple of two decimal values. The values represent the percentage'
        ' of viewport width and the percentage of viewport height.'
    )

    width: Optional[float] = Field(
        description=' A decimal number representing the percentage of viewport width'
        ' that will be used to define the width of the legend.'
    )

    height: Optional[float] = Field(
        description='A decimal number representing the percentage of viewport height'
        'that will be used to define the height of the legend.'
    )

    number_of_colors: Optional[int] = Field(
        description='An integer representing the number of colors in a legend.'
    )

    number_of_labels: Optional[int] = Field(
        description='An integer representing the number of text labels on a legend.'
    )

    label_format: Optional[str] = Field(
        description='Format of legend labels.'
    )

    label_position: Optional[int] = Field(
        description='0 or 1 to decide whether the legend title and the legend labels'
        ' will precede the legend or not.'
    )

    label_fonts: Optional[FontConfig] = Field(
        description='Font parameters for the fonts to be used for the labels on the'
        ' legend.'
    )

    title_fonts: Optional[FontConfig] = Field(
        description='Font parameters for the fonts to be used in the title of the'
        ' legend.'
    )

    @validator('colors')
    def validate_colors(cls, v: str) -> str:
        colors = dir(Colors)[4:]
        if v.lower() in colors:
            return v
        else:
            raise ValueError(
                f'Colors must be a string from {tuple(colors)}. Instead got'
                f' {v}.'
            )

    @validator('orientation')
    def validate_orientation(cls, v: str) -> str:
        orientations = ('horizontal', 'vertical')
        if v.lower() in orientations:
            return v
        else:
            raise ValueError(
                f'Orientation must be from {orientations}. Instead got {v}.'
            )

    @validator('label_format')
    def validate_label_format(cls, v: str) -> str:
        label_formats = dir(LabelFormat)[4:]
        if v in label_formats:
            return v
        else:
            raise ValueError(
                f'Label format must be from {label_formats}. Instead got {v}.'
            )


class DataConfig(BaseModel):
    """Config for each dataset you'd like to load on a honeybee-vtk model."""

    name: str = Field(
        description='Name to be given to data. Example, "Daylight-Factor".'
    )

    object_type: str = Field(
        description='The name of the model object on which you would like to map this'
        ' data.'
    )

    file_paths: List[str] = Field(
        description='List of paths to the file or files that you are trying to use as'
        ' data.'
    )

    legend_parameters: Optional[LegendConfig] = Field(
        description='Legend parameters to create legend out of the this dataset.'
    )

    @validator('object_type')
    def validate_object(cls, v: str) -> str:
        if v in model_dataset_names:
            return v
        else:
            raise ValueError(
                f'Object name should be from these {model_dataset_names}.'
                f' Instead got {v}.'
            )

    @validator('file_paths')
    def validate_paths(cls, v: List[str]) -> List[str]:
        if all([Path(path).is_file() for path in v]):
            return v
        else:
            paths = tuple([path for path in v if not Path(path).is_file()])
            raise ValueError(
                f'Following file paths are not valid {paths}.'
            )
