"""Data json schema and validation."""

from pathlib import Path
from typing import Dict, List
from pydantic import BaseModel, validator, Field
from .model import Model
from .vtkjs.schema import SensorGridOptions


class DataConfig(BaseModel):

    name: str = Field(
        description='Name to be give to data. Example, "Daylight-Factor".'
    )

    object_name: str = Field(
        description='The name of the model object on which you would like to map this'
        ' data.'
    )

    delimiter: str = Field(
        description='The delimiter used in the file or files that you are trying to'
        ' use as data.'
    )

    file_paths: List[str] = Field(
        description='List of paths to the file or files that you are trying to use as'
        ' data.'
    )

    @validator('object_name')
    def validate_object(cls, v):
        accepted_object_names = (
            'walls', 'apertures', 'shades', 'doors', 'floors', 'roof_ceilings',
            'air_boundaries', 'sensor_grids')
        if v in accepted_object_names:
            return v
        else:
            raise ValueError(
                f'Object name should be from these {accepted_object_names}.'
                f' Instead got {v}.'
            )

    @validator('delimiter')
    def validate_delimiter(cls, v):
        accepted_delimiters = (',', ' ', '    ', ';', '|')
        if v in accepted_delimiters:
            return v
        else:
            raise ValueError(
                f'The delimiter must be from one of these {accepted_delimiters}.'
                f' Instead got {v}.'
            )

    @validator('file_paths')
    def validate_paths(cls, v):
        if all([Path(path).is_file() for path in v]):
            return v
        else:
            raise ValueError(
                'File paths are not valid.'
            )

    def cross_check_data(self, hbjson: str):

        model = Model.from_hbjson(hbjson=hbjson, load_grids=SensorGridOptions.Mesh)

        if self.object_name == 'grid':
            grid_names = [grid.identifier for grid in model.sensor_grids.data]
            file_names = [Path(path).name.split('.')[0] for path in self.file_paths]
            if len(grid_names) != len(file_names) or grid_names != file_names:
                raise ValueError(
                    'The file names must match the grid identifiers in HBJSON.'
                )
            return True

        elif self.object_name in (
            'walls', 'apertures', 'shades', 'doors', 'floors', 'roof_ceilings',
            'air_boundaries')
        pass


class Json_schema(BaseModel):

    data: Dict[str: DataConfig] = Field(
        description='A dictionary to introduce data that you would like to mount.'
        ' The key must be any text and the value must be DataConfig.'
    )


def check_json(file_path):
    pass
