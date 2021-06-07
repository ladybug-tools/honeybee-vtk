"""Data json schema and validation."""

import json
from pathlib import Path
from typing import Dict, List
from pydantic import BaseModel, validator, Field
from enum import Enum
from .model import Model
from .vtkjs.schema import SensorGridOptions


class Data(BaseModel):

    acceptable_object_names = (
        'walls', 'apertures', 'shades', 'doors', 'floors', 'roof_ceilings',
        'air_boundaries', 'sensor_grids')

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
        if v in cls.acceptable_object_names:
            return v
        else:
            raise ValueError(
                f'Object name should be from these {cls.acceptable_object_names}.'
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

    def cross_check_data(self, model):
        class ModelData(Enum):
            walls = model.walls.data
            apertures = model.apertures.data
            shades = model.shades.data
            doors = model.doors.data
            floors = model.floors.data
            roof_ceilings = model.roof_ceilings.data
            air_boundaries = model.air_boundaries.data

        # if object name is "grid" check that the name of files match the grid names
        if self.object_name == 'sensor_grids':
            grid_names = [grid.identifier for grid in model.sensor_grids.data]
            file_names = [Path(path).name.split('.')[0] for path in self.file_paths]
            if len(grid_names) != len(file_names) or grid_names != file_names:
                raise ValueError(
                    'The number of files and the file names must match the grid'
                    ' identifiers in HBJSON.'
                )
            return True

        # if object_name is other than grid check that length of data matches the length
        # of data in the model for that object.
        elif self.object_name in self.acceptable_object_names[:-1]:

            if len(self.file_paths) == 0:
                raise ValueError(
                    'File path not found in the config file.'
                )
            elif len(self.file_paths) > 0:
                raise ValueError(
                    'Only one file path needs to be provided in order to load data on'
                    f' {self.object_name}. Multiple files are provided in the config'
                    ' file.'
                )

            file = open(self.file_paths[0], "r")
            nonempty_line_count = len(
                [line.strip("\n") for line in file if line != "\n"]
            )
            file.close()

            if nonempty_line_count != len(ModelData[self.object_name].value):
                raise ValueError(
                    'The length of data in the file does not match the number of faces'
                    ' in the model.'
                )
            return True


class DataConfig(BaseModel):

    data: Dict[str, Data] = Field(
        description='A dictionary to introduce data that you would like to mount.'
        ' The key must be any text and the value must be DataConfig.'
    )

    def check_data(self, hbjson):
        model = Model.from_hbjson(hbjson=hbjson, load_grids=SensorGridOptions.Mesh)
        return all([val.cross_check_data(model) for val in self.data.values()])


def check_data_config(config_path, hbjson):

    path = Path(config_path)
    assert path.exists(), 'Not a valid path'

    try:
        with open(config_path) as fh:
            config = json.load(fh)
    except json.decoder.JSONDecodeError:
        raise ValueError(
            'Not a valid json file.'
        )
    else:
        # Parse config.json using config schema
        json_obj = DataConfig.parse_file(path)
        if json_obj.check_data(hbjson):
            return json_obj.dict(exclude_none=True)
