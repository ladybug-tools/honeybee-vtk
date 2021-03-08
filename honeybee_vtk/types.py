"""An extension of VTK PolyData objects.

The purpose of creating these extensions is to add metadata to object itself. This will
work fine for the purpose of exporting the geometries and finding the type for each
object but it will not be useful for passing them to the exported VTK file itself.

For that purpose we should start to look into FieldData:
https://lorensen.github.io/VTKExamples/site/Cxx/PolyData/FieldData/
"""
import enum
import vtk
from typing import Union, List
import pathlib


class VTKWriters(enum.Enum):
    """Vtk writers."""
    legacy = 'vtk'
    ascii = 'vtk'
    binary = 'vtp'


class PolyData(vtk.vtkPolyData):
    """A thin wrapper around vtk.vtkPolyData.

    PolyData has an additional meta_data dictionary.
    """
    def __init__(self) -> None:
        super().__init__()
        self.identifier = None
        self.display_name = None
        self.type = None
        self.meta_data = {}

    @staticmethod
    def _resolve_array_type(data):
        if isinstance(data, float):
            return vtk.vtkFloatArray()
        elif isinstance(data, int):
            return vtk.vtkIntArray()
        else:
            raise ValueError(f'Unsupported input data type: {type(data)}')

    def add_data(self, data: List, *, name=None, cell=True):
        """Add a list of data to a vtkPolyData.

        Data can be added to cells or points. By default the data will be added to cells.
        """
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

    def color_by(self, name: str, cell=True) -> None:
        """Set the name for active data that should be used to color PolyData."""
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

    def to_vtkjs(self, target_folder, name):
        pass


class PolyDataJoined(vtk.vtkAppendPolyData):
    """A thin wrapper around vtk.vtkPolyData.

    PolyDataJoined has an additional meta_data dictionary.
    """
    def __init__(self) -> None:
        super().__init__()
        # just keep track of all the assigned information
        self.identifier = None
        self.display_name = None
        self.meta_data = {}

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


def _write_to_file(
    polydata: Union[PolyData, PolyDataJoined], target_folder: str, file_name: str,
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


def _write_to_folder(polydata: Union[PolyData, PolyDataJoined], target_folder: str):
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
