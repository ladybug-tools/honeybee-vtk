"""Data json schema and validation."""


from pathlib import Path
from typing import List
from pydantic import BaseModel, validator, Field
from .types import model_dataset_names


class DataConfig(BaseModel):
    """Config for each dataset you'd like to load on a honeybee-vtk model."""

    name: str = Field(
        description='Name to be give to data. Example, "Daylight-Factor".'
    )

    object_type: str = Field(
        description='The name of the model object on which you would like to map this'
        ' data.'
    )

    file_paths: List[str] = Field(
        description='List of paths to the file or files that you are trying to use as'
        ' data.'
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
