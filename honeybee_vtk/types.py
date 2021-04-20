"""An extension of VTK PolyData objects.

The purpose of creating these extensions is to add metadata to object itself. This will
work fine for the purpose of exporting the geometries and finding the type for each
object but it will not be useful for passing them to the exported VTK file itself.

For that purpose we should start to look into FieldData:
https://lorensen.github.io/VTKExamples/site/Cxx/PolyData/FieldData/

"""
import enum
from typing import Dict, Union, List
import pathlib

import vtk

from ladybug.color import Color, Colorset

from .vtkjs.schema import DataSetProperty, DataSet, DisplayMode, DataSetMapper


class VTKWriters(enum.Enum):
    """Vtk writers."""
    legacy = 'vtk'
    ascii = 'vtp'
    binary = 'vtp'


COLORSET = Colorset()


class DataFieldInfo:
    """Information for a data field."""
    def __init__(self, name='default', range=None, colors=None, per_face=True) -> None:
        self.name = name
        self.data_range = range or (0, 100)
        self.colors = colors or COLORSET.ecotect()
        self.per_face = per_face

    def color_range(self):
        """A VTK lookup table that acts as a color range."""
        minimum, maximum = self.data_range
        color_values = self.colors
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


class PolyData(vtk.vtkPolyData):
    """A thin wrapper around vtk.vtkPolyData.

    PolyData has additional fields for metadata information.
    """
    def __init__(self) -> None:
        super().__init__()
        self.identifier = None
        self.display_name = None
        self.type = None
        self._fields = {}  # keep track of information for each data field.

    @staticmethod
    def _resolve_array_type(data):
        if isinstance(data, float):
            return vtk.vtkFloatArray()
        elif isinstance(data, int):
            return vtk.vtkIntArray()
        else:
            raise ValueError(f'Unsupported input data type: {type(data)}')

    @property
    def data_fields(self) -> Dict[str, DataFieldInfo]:
        """Get data fields for this Polydata."""
        return self._fields

    def add_data(self, data: List, name, *, cell=True, color_set=None, data_range=None):
        """Add a list of data to a vtkPolyData.

        Data can be added to cells or points. By default the data will be added to cells.

        Args:
            data: A list of values. The length of the data should match the length of
                DataCells or DataPoints in Polydata.
            name: Name of data (e.g. Useful Daylight Autonomy.)
            cell: A Boolean to indicate if the data is per cell or per point. In
                most cases except for sensor points that are loaded as sensors the data
                are provided per cell.
            color_set: A Ladybug Tools color set. Use COLORSET to set colorset for data.
            data_range: A list with two values for minimum and maximum values for legend.
        """
        assert name not in self._fields, \
            f'A data filed by name "{name}" already exist. Try a different name.'

        if isinstance(data[0], (list, tuple)):
            values = self._resolve_array_type(data[0][0])
            values.SetNumberOfComponents(len(data[0]))
            values.SetNumberOfTuples(len(data))
            iterator = True
        else:
            values = self._resolve_array_type(data[0])
            iterator = False

        if name:
            values.SetName(name)

        if iterator:
            # NOTE: This is my (mostapha's) understanding from the original code for
            # tuple data. This needs to be tested.
            for d in data:
                values.InsertNextValue(*d)
        else:
            for d in data:
                values.InsertNextValue(d)

        if cell:
            self.GetCellData().AddArray(values)
        else:
            self.GetPointData().AddArray(values)

        self.Modified()

        # store information
        if not data_range:
            data_range = tuple(values.GetRange())
        if not color_set:
            color_set = COLORSET.ecotect()

        self._fields[name] = DataFieldInfo(name, data_range, color_set, cell)

    def color_by(self, name: str, cell=True) -> None:
        """Set the name for active data that should be used to color PolyData."""
        assert name in self._fields, \
            f'{name} is not a valid data field for this PolyData. Available ' \
            f'data fields are: {list(self._fields)}'

        if cell:
            self.GetCellData().SetActiveScalars(name)
        else:
            self.GetPointData().SetActiveScalars(name)
        self.Modified()

    def to_vtk(self, target_folder, name, ascii=False):
        """Write to a VTK file.

        The file extension will be set to vtk for ASCII format and vtp for binary format.
        """
        writer = VTKWriters.ascii if ascii else VTKWriters.binary
        return _write_to_file(self, target_folder, name, writer=writer)

    def to_folder(self, target_folder='.'):
        """Write data to a folder with a JSON meta file.

        This method generates a folder that includes a JSON meta file along with all the
        binary arrays written as standalone binary files.

        The generated format can be used by vtk.js using the reader below
        https://kitware.github.io/vtk-js/examples/HttpDataSetReader.html

        Args:
            target_folder: Path to target folder. Default: .

        """
        return _write_to_folder(self, target_folder)


class JoinedPolyData(vtk.vtkAppendPolyData):
    """A thin wrapper around vtk.vtkAppendPolyData."""
    def __init__(self) -> None:
        super().__init__()

    @classmethod
    def from_polydata(cls, polydata: List[PolyData]):
        """Join several polygonal datasets.

        This function merges several polygonal datasets into a single polygonal datasets.
        All geometry is extracted and appended, but point and cell attributes (i.e.,
        scalars, vectors, normals) are extracted and appended only if all datasets have
        the point and/or cell attributes available. (For example, if one dataset has
        point scalars but another does not, point scalars will not be appended.)
        """
        joined_polydata = cls()

        for vtk_polydata in polydata:
            joined_polydata.AddInputData(vtk_polydata)

        joined_polydata.Update()

        return joined_polydata

    def append(self, polydata: PolyData) -> None:
        """Append a new polydata to current data."""
        self.AddInputData(polydata)
        self.Update()

    def extend(self, polydata: List[PolyData]) -> None:
        """Extend a list of new polydata to current data."""
        for data in polydata:
            self.AddInputData(data)
        self.Update()

    def to_vtk(self, target_folder, name, ascii=False):
        """Write to a VTK file.

        The file extension will be set to vtk for ASCII format and vtp for binary format.
        """
        writer = VTKWriters.ascii if ascii else VTKWriters.binary
        return _write_to_file(self, target_folder, name, writer=writer)

    def to_folder(self, target_folder='.'):
        """Write data to a folder with a JSON meta file.

        This method generates a folder that includes a JSON meta file along with all the
        binary arrays written as standalone binary files.

        The generated format can be used by vtk.js using the reader below
        https://kitware.github.io/vtk-js/examples/HttpDataSetReader.html

        Args:
            target_folder: Path to target folder. Default: .

        """
        return _write_to_folder(self, target_folder)


class ModelDataSet:
    """A dataset object in honeybee VTK model.

    This data set holds the PolyData objects as well as representation information
    for those PolyData. All the objects in ModelDataSet will have the same
    representation.
    """
    def __init__(self, name, data: List[PolyData] = None, color: Color = None) -> None:
        self.name = name
        self.data = data or []
        self.color = color
        self.display_mode = DisplayMode.Shaded
        self.color_by = None

    @property
    def fields_info(self) -> dict:
        return {} if not self.data else self.data[0]._fields

    @property
    def active_field_info(self) -> DataFieldInfo:
        """Get information for active field info.

        It will be the field info for the field that is set in color_by. If color_by
        is not set the first field will be used. If no field is available a default
        field will be generated.

        """
        info = self.fields_info
        color_by = self.color_by
        if not info:
            return DataFieldInfo()
        if not color_by:
            return next(info.values())
        return info[color_by]

    def add_data_fields(
        self, data: List[List], name: str, per_face: bool = True, color_set=None,
        data_range=None
            ):
        """Add data fields to PolyData objects in this dataset.

        Use this method to add data like temperature or illuminance values to PolyData
        objects. The length of the input data should match the length of the data in
        DataSet.

        Args:
            data: A list of list of values. There should be a list per data in DataSet.
                The order of data should match the order of data in DataSet. You can
                use data.identifier to match the orders before assigning them to DataSet.
            name: Name of data (e.g. Useful Daylight Autonomy.)
            per_face: A Boolean to indicate if the data is per face or per point. In
                most cases except for sensor points that are loaded as sensors the data
                are provided per face.
            color_set: A Ladybug Tools color set. Use COLORSET to set colorset for data.
            data_range: A list with two values for minimum and maximum values for legend.

        """
        assert len(self.data) == len(data), \
            f'Length of input data {len(data)} does not match the length of polydata ' \
            f'in this dataset {len(self.data)}.'

        for count, d in enumerate(data):
            self.data[count].add_data(
                d, name=name, cell=per_face, color_set=color_set, data_range=data_range
            )

    @property
    def is_empty(self):
        return len(self.data) == 0

    @property
    def color(self) -> Color:
        """Diffuse color.

        By default the dataset will be colored by this color unless color_by property
        is set to a dataset value.
        """
        return self._color

    @color.setter
    def color(self, value: Color):
        self._color = value if value else Color(204, 204, 204, 255)

    @property
    def color_by(self) -> str:
        """Set the field that the DataSet should colored-by when exported to vtkjs.

        By default the dataset will be colored by surface color and not data fields.
        """
        return self._color_by

    @color_by.setter
    def color_by(self, value: str):
        fields_info = self.fields_info
        if not value:
            self._color_by = None
        else:
            assert value in fields_info, \
                f'{value} is not a valid data field for this ModelDataSet. Available ' \
                f'data fields are: {list(fields_info.keys())}'

        for data in self.data:
            data.color_by(value, fields_info[value].per_face)

        self._color_by = value

    @property
    def opacity(self) -> float:
        """Visualization opacity."""
        return self.color.a

    @property
    def display_mode(self) -> DisplayMode:
        """Display model (AKA Representation) mode in VTK Glance viewer.

        Valid values are:
            * Surface / Shaded
            * SurfaceWithEdges
            * Wireframe
            * Points

        Default is 0 for Surface mode.

        """
        return self._display_mode

    @display_mode.setter
    def display_mode(self, mode: DisplayMode = DisplayMode.Surface):
        self._display_mode = mode

    @property
    def edge_visibility(self) -> bool:
        """Edge visibility.

        The edges will be visible in Wireframe or SurfaceWithEdges modes.
        """
        if self.display_mode.value in (0, 2):
            return False
        else:
            return True

    def to_folder(self, folder, sub_folder=None) -> str:
        """Write data information to a folder.

        Args:
            folder: Target folder to write the dataset.
            sub_folder: Subfolder name for this dataset. By default it will be set to
                the name of the dataset.
        """
        sub_folder = sub_folder or self.name
        target_folder = pathlib.Path(folder, sub_folder)

        if len(self.data) == 0:
            print(f'ModelDataSet: {self.name} has no data to be exported to folder.')
            return
        elif len(self.data) == 1:
            data = self.data[0]
        else:
            data = JoinedPolyData.from_polydata(self.data)
        return _write_to_folder(data, target_folder.as_posix())

    # TODO: export color-range information for each dataset
    # each dataset has its own information. If we can only have one then we should use
    # the information for color_by field.
    def as_data_set(self, url=None) -> DataSet:
        """Convert to a vtkjs DataSet object.

        Args:
            url: Relative path to where PolyData information should be sourced from.
                By default url will be set to ModelDataSet name assuming data is dumped
                to a folder with the same name.

        """
        prop = {
            'representation': min(self.display_mode.value, 2),
            'edgeVisibility': int(self.edge_visibility),
            'diffuseColor': [self.color.r / 255, self.color.g / 255, self.color.b / 255],
            'opacity': self.opacity / 255
        }

        ds_prop = DataSetProperty.parse_obj(prop)

        mapper = DataSetMapper()
        if self.color_by is not None:
            mapper.colorByArrayName = self.color_by

        data = {
            'name': self.name,
            'httpDataSetReader': {'url': url if url is not None else self.name},
            'property': ds_prop.dict(),
            'mapper': mapper.dict()
        }

        return DataSet.parse_obj(data)

    def __repr__(self) -> str:
        return f'ModelDataSet: {self.name}' \
            '\n  DataSets: {len(self.data)}\n  Color:{self.color}'


def _write_to_file(
    polydata: Union[PolyData, JoinedPolyData], target_folder: str, file_name: str,
    writer: VTKWriters = VTKWriters.binary
        ):
    """Write vtkPolyData to a file."""
    # Write as a vtk file
    extension = writer.value
    if writer.name == 'legacy':
        _writer = vtk.vtkPolyDataWriter()
    else:
        _writer = vtk.vtkXMLPolyDataWriter()
        if writer.name == 'binary':
            _writer.SetDataModeToBinary()
        else:
            _writer.SetDataModeToAscii()

    file_path = pathlib.Path(target_folder, f'{file_name}.{extension}')
    _writer.SetFileName(file_path.as_posix())
    if isinstance(polydata, vtk.vtkPolyData):
        _writer.SetInputData(polydata)
    else:
        _writer.SetInputConnection(polydata.GetOutputPort())

    _writer.Write()
    return file_path.as_posix()


def _write_to_folder(polydata: Union[PolyData, JoinedPolyData], target_folder: str):
    """Write PolyData to a folder using vtkJSONDataSetWriter."""
    writer = vtk.vtkJSONDataSetWriter()
    folder = pathlib.Path(target_folder)
    folder.mkdir(parents=True, exist_ok=True)
    writer.SetFileName(folder.as_posix())

    if isinstance(polydata, vtk.vtkPolyData):
        writer.SetInputData(polydata)
    else:
        writer.SetInputConnection(polydata.GetOutputPort())
    writer.Write()
    return folder.as_posix()
