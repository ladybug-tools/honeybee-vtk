"""Data json schema and validation."""

import json
from json.decoder import JSONDecodeError
from pathlib import Path
from typing import Dict, List
from pydantic import BaseModel, validator, Field
from pydantic.errors import JsonError
from .model import Model
from .types import AcceptedValues


class Data(BaseModel):
    """COnfig for data."""

    name: str = Field(
        description='Name to be give to data. Example, "Daylight-Factor".'
    )

    object_name: str = Field(
        description='The name of the model object on which you would like to map this'
        ' data.'
    )

    file_paths: List[str] = Field(
        description='List of paths to the file or files that you are trying to use as'
        ' data.'
    )

    @validator('object_name')
    def validate_object(cls, v: str) -> str:
        if v in AcceptedValues.names.value:
            return v
        else:
            raise ValueError(
                f'Object name should be from these {AcceptedValues.names.value}.'
                f' Instead got {v}.'
            )

    @validator('file_paths')
    def validate_paths(cls, v: List[str]) -> List[str]:
        if all([Path(path).is_file() for path in v]):
            return v
        else:
            raise ValueError(
                'File paths are not valid.'
            )

    def cross_check_data(self, model: Model) -> bool:
        """Cross check data with model.

        For grids, it will be checked if the number of data files and the names of the
        data files match with the grid identifiers. For other than grid objects, it will
        be checked that only one data file is provided and the length of the data file
        matches the length of Polydata in the model.

        Args:
            model: A honeybee-vtk model object.

        Returns:
            A boolean value.
        """

        # if object name is "grid" check that the name of files match the grid names
        if self.object_name == AcceptedValues.names.value[-1]:

            assert len(model.sensor_grids.data) > 0, 'Sensor grids are not loaded on'\
                ' this model. Reload them using grid options.'

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
        elif self.object_name in AcceptedValues.names.value[:-1]:

            if len(self.file_paths) == 0:
                raise ValueError(
                    'File path not found in the config file.'
                )
            elif len(self.file_paths) > 1:
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

            if nonempty_line_count != len(
                    model.get_modeldataset_from_string(self.object_name).data):
                raise ValueError(
                    'The length of data in the file does not match the number of'
                    f' {self.object_name} objects in the model.'
                )
            return True

        else:
            raise ValueError(
                ' object_name must be from one of these'
                f' {AcceptedValues.names.value}. Instead got {self.object_name}.'
            )


class DataConfig(BaseModel):
    """Config for the whole data config file."""

    data: Dict[str, Data] = Field(
        description='A dictionary to introduce data that you would like to mount.'
        ' The key must be any text and the value must be DataConfig.'
    )

    def check_data(self, model: Model) -> bool:
        return all([val.cross_check_data(model) for val in self.data.values()])


def check_data_config(config_path: str, model: Model) -> Dict[str, DataConfig]:
    """Validate the data config file.

    Args:
        config_path: File path to the data config file.
        model: A honeybee-vtk model object.

    Returns:
        Data config as a dictionary.
    """
    # Check if path is valid
    path = Path(config_path)
    if not path.exists():
        raise FileExistsError(
            f'{config_path} is not a valid path.'
        )

    # Check if json is valid
    try:
        with open(config_path) as fh:
            config = json.load(fh)
    except json.decoder.JSONDecodeError:
        raise TypeError(
            'Not a valid json file.'
        )

    # Check if schema is valid
    else:
        json_obj = DataConfig.parse_file(path)
        if json_obj.check_data(model):
            return json_obj.dict(exclude_none=True)
        else:
            raise ValueError(
                'Validation failed.'
            )
