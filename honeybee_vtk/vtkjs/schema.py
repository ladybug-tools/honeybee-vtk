"""Schema for VTKJS objects."""
import json
import pathlib
from typing import Dict, List
import enum

from pydantic import BaseModel, Field, validator


class DisplayMode(enum.Enum):
    """Display mode."""
    Shaded = 2
    Surface = 2
    SurfaceWithEdges = 3
    Wireframe = 1
    Points = 0


class SensorGridOptions(enum.Enum):
    """Settings for loading sensor grids."""
    Ignore = 0  # no loading
    Sensors = 1  # load them as sensor points
    Mesh = 2  # load them as mesh


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


class IndexJSON(BaseModel):
    """VTKJS index class.

    These information will be translated to an index.json file.
    """
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
