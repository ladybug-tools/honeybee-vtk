import json
import pathlib
from typing import Dict, List

from pydantic import BaseModel, Field, validator


_COLORSET = {
    'Wall': [0.901, 0.705, 0.235, 1],
    'Aperture': [0.250, 0.705, 1, 0.5],
    'Door': [0.627, 0.588, 0.392, 1],
    'Shade': [0.470, 0.294, 0.745, 1],
    'Floor': [1, 0.501, 0.501, 1],
    'RoofCeiling': [0.501, 0.078, 0.078, 1],
    'AirBoundary': [1, 1, 0.784, 1],
    'Grid': [0.925, 0.250, 0.403, 1]
}


def color_by_type(face_type) -> List:
    """Get the default color based of face type.

    Use these colors to generate visualizations that are familiar for Ladybug Tools
    users.
    """
    return _COLORSET.get(face_type, [1, 1, 1, 1])


class Camera(BaseModel):
    """Camera in vtkjs viewer."""
    focalPoint: List[float] = Field(
        [2.5, 5, 1.5],
        description='Camera focal point.', max_items=3, min_items=3
    )
    position: List[float] = Field(
        [19.3843, -6.75305, 10.2683],
        description='Camera position.', max_items=3, min_items=3
    )
    viewUp: List[float] = Field(
        [-0.303079, 0.250543, 0.919441],
        description='View up vector.', max_items=3, min_items=3
    )


class DataSetResource(BaseModel):
    """Path to a data resource."""
    url: str = Field(
        ..., description='Relative path to data resource.'
    )


class DataSetActor(BaseModel):
    """A Dataset actor."""
    origin: List[float] = Field([0, 0, 0])
    scale: List[float] = Field([1, 1, 1])
    position: List[float] = Field([0, 0, 0])


class DataSetMapper(BaseModel):
    colorByArrayName: str = Field('')
    colorMode: int = Field(0)
    scalarMode: int = Field(4)


class DataSetProperty(BaseModel):
    representation: int = Field(2)
    edgeVisibility: int = Field(0)
    diffuseColor: List[float] = Field(
        [0.8, 0.8, 0.8],
        description='Surface color.', max_items=3, min_items=3
    )
    pointSize: int = Field(5)
    opacity: float = Field(1)


class DataSet(BaseModel):
    """A VTKJS dataset."""
    name: str = Field(..., description='DataSet name.')
    type: str = Field('httpDataSetReader')  # I don't know enough about this field!
    httpDataSetReader: DataSetResource = Field(...)
    actor: DataSetActor = Field(DataSetActor())
    actorRotation: List[float] = Field(
        [0, 0, 0, 1],
        description='Actor rotation axis.', max_items=4, min_items=4
    )
    mapper: DataSetMapper = Field(DataSetMapper())
    property: DataSetProperty = Field(DataSetProperty())


class ViewerSettings(BaseModel):
    version = 1
    background: List[float] = Field(
        [1, 1, 1],
        description='Background color.', max_items=3, min_items=3
    )
    camera: Camera = Field(
        Camera(),
        description='Initial camera in the viewer.'
    )
    centerOfRotation: List[float] = Field(
        [2.5, 5, 1.5],
        description='X, Y, Z for center of rotation.', max_items=3, min_items=3
    )
    scene: List[DataSet] = Field(
        None, description='List of data set in viewer.'
    )
    lookupTables: Dict = Field(
        None
    )

    @validator('scene', always=True)
    def empty_list(cls, v):
        return [] if v is None else v

    @validator('lookupTables', always=True)
    def empty_dict(cls, v):
        return {} if v is None else v

    def to_json(self, folder: str) -> str:
        """Write the settings as index.json."""
        data = self.dict()
        target_folder = pathlib.Path(folder)
        target_folder.mkdir(parents=True, exist_ok=True)
        index_file = pathlib.Path(target_folder, 'index.json')
        index_file.write_text(json.dumps(data))
        return index_file.as_posix()
