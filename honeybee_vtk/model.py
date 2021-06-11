"""A VTK representation of HBModel."""

from __future__ import annotations
from json.decoder import JSONDecodeError
import pathlib
import shutil
import webbrowser
import tempfile
import os
import warnings
import json
from collections import defaultdict
from typing import Dict, List
from honeybee.facetype import face_types
from honeybee.model import Model as HBModel
from ladybug.color import Color
from .camera import Camera
from .types import ModelDataSet, PolyData
from .to_vtk import convert_aperture, convert_face, convert_room, convert_shade, \
    convert_sensor_grid
from .vtkjs.schema import IndexJSON, DisplayMode, SensorGridOptions
from .vtkjs.helper import convert_directory_to_zip_file, add_data_to_viewer
from .types import model_dataset_names
from ._helper import get_min_max, get_line_count
from .config import DataConfig


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


DATA_SETS = {
    'Aperture': 'apertures', 'Door': 'doors', 'Shade': 'shades',
    'Wall': 'walls', 'Floor': 'floors', 'RoofCeiling': 'roof_ceilings',
    'AirBoundary': 'air_boundaries'
}


class Model(object):
    """A honeybee-vtk model.

    The model objects are accessible based on their types:

        * apertures
        * doors
        * shades
        * walls
        * floors
        * roof_ceilings
        * air_boundaries
        * sensor_grids

    You can control the style for each type separately.

    """

    def __init__(
            self, model: HBModel,
            load_grids: SensorGridOptions = SensorGridOptions.Ignore) -> None:
        """Instantiate a honeybee-vtk model object.

        Args:
            model : A text string representing the path to the hbjson file.
            load_grids: A SensorGridOptions object. Defaults to SensorGridOptions.Ignore
                which will ignore the grids in hbjson and will not load them in the
                honeybee-vtk model.
        """
        super().__init__()
        # apertures and orphaned apertures
        self._apertures = \
            ModelDataSet('Aperture', color=self.get_default_color('Aperture'))
        # doors and orphaned doors
        self._doors = ModelDataSet('Door', color=self.get_default_color('Door'))
        # shades and orphaned shades
        self._shades = ModelDataSet('Shade', color=self.get_default_color('Shade'))
        # face objects based on type
        self._walls = ModelDataSet('Wall', color=self.get_default_color('Wall'))
        self._floors = ModelDataSet('Floor', color=self.get_default_color('Floor'))
        self._roof_ceilings = \
            ModelDataSet('RoofCeiling', color=self.get_default_color('RoofCeiling'))
        self._air_boundaries = \
            ModelDataSet('AirBoundary', color=self.get_default_color('AirBoundary'))
        self._sensor_grids = ModelDataSet('Grid', color=self.get_default_color('Grid'))
        self._cameras = []
        self._convert_model(model)
        self._load_grids(model, load_grids)
        self._load_cameras(model)
        self._sensor_grids_option = load_grids  # keep this for adding data

    @classmethod
    def from_hbjson(cls, hbjson: str,
                    load_grids: SensorGridOptions = SensorGridOptions.Ignore) -> Model:
        """Translate hbjson to a honeybee-vtk model.

        Args:
            model : A text string representing the path to the hbjson file.
            load_grids: A SensorGridOptions object. Defaults to SensorGridOptions.Ignore
                which will ignore the grids in hbjson and will not load them in the
                honeybee-vtk model.

        Returns:
            A honeybee-vtk model object.
        """
        hb_file = pathlib.Path(hbjson)
        assert hb_file.is_file(), f'{hbjson} doesn\'t exist.'
        model = HBModel.from_hbjson(hb_file.as_posix())
        return cls(model, load_grids)

    @property
    def walls(self) -> ModelDataSet:
        """Model walls."""
        return self._walls

    @property
    def apertures(self) -> ModelDataSet:
        """Model aperture."""
        return self._apertures

    @property
    def shades(self) -> ModelDataSet:
        """Model shades."""
        return self._shades

    @property
    def doors(self) -> ModelDataSet:
        """Model doors."""
        return self._doors

    @property
    def floors(self) -> ModelDataSet:
        """Model floors."""
        return self._floors

    @property
    def roof_ceilings(self) -> ModelDataSet:
        """Roof and ceilings."""
        return self._roof_ceilings

    @property
    def air_boundaries(self) -> ModelDataSet:
        """Air boundaries."""
        return self._air_boundaries

    @property
    def sensor_grids(self) -> ModelDataSet:
        """Sensor grids."""
        return self._sensor_grids

    @property
    def cameras(self):
        """List of Camera objects attached to this Model object."""
        return self._cameras

    def get_modeldataset_from_string(self, text: str) -> ModelDataSet:
        """Get a ModelDataSet object from a model using a text string.

        Args:
            text: A text string such as "walls", "shades"

        Returns:
            A ModelDataSet object.
        """
        if text not in model_dataset_names:
            raise ValueError(
                f'Text must be one of the {model_dataset_names}.'
                f' Instead got {text}.'
            )
        ds = {ds.name.lower(): ds for ds in self}
        return ds[text]

    def __iter__(self):
        """This dunder method makes this class an iterator object.

        Due to this method, you can access apertures, walls, shades, doors, floors,
        roof_ceilings, air_boundaries and sensor_grids in a model
        like items of a list in Python. Which means, you can use loops on these objects
        of a model.
        """
        for dataset in (
            self.apertures, self.walls, self.shades, self.doors, self.floors,
            self.roof_ceilings, self.air_boundaries, self.sensor_grids
        ):
            yield dataset

    def _load_grids(self, model: HBModel, grid_options: SensorGridOptions) -> None:
        """Load sensor grids."""
        if grid_options == SensorGridOptions.Ignore:
            return
        if hasattr(model.properties, 'radiance'):
            for sensor_grid in model.properties.radiance.sensor_grids:
                self._sensor_grids.data.append(
                    convert_sensor_grid(sensor_grid, grid_options)
                )

    def _load_cameras(self, model: HBModel) -> None:
        """Load radiance views."""
        if len(model.properties.radiance.views) > 0:
            for view in model.properties.radiance.views:
                self._cameras.append(Camera.from_view(view))
        else:
            warnings.warn(
                'views not found in HBJSON.'
            )

    def _validate_data(self, data: DataConfig) -> bool:
        """Cross check data with model.

        For grids, it will be checked if the number of data files and the names of the
        data files match with the grid identifiers. For other than grid objects, it will
        be checked that only one data file is provided and the length of the data file
        matches the length of Polydata in the model. This is a helper method to the
        public load_config method.

        Args:
            data: A DataConfig object.

        Returns:
            A boolean value.
        """

        # if object name is "grid" check that the name of files match the grid names
        if data.object_type == model_dataset_names[-1]:

            # make sure grids are loaded on the model if grid data is to be mounted
            assert len(self.sensor_grids.data) > 0, 'Sensor grids are not loaded on'\
                ' this model. Reload them using grid options.'

            grid_names = [grid.identifier for grid in self.sensor_grids.data]
            file_names = [pathlib.Path(path).stem for path in data.file_paths]
            names_in_grids = all([name in grid_names for name in file_names])

            # the number of data files must not exceed the number of grids
            if len(file_names) > len(grid_names):
                raise ValueError(
                    f'There are only {len(grid_names)} grids in the model and the'
                    f' identifiers of those grids are {tuple(grid_names)}.'
                )

            # TODO: remove this check in the next iteration
            # make sure there's one file for each grid in the model
            if not names_in_grids:
                raise ValueError(
                    'Make sure the file names match the grid identifiers. The'
                    f' identifiers of the grids in the model are {tuple(grid_names)}.'
                )

            # make sure length of each file matches the number of sensors in grid
            file_lengths = [get_line_count(file_path) for file_path in data.file_paths]
            num_sensors = [polydata.GetNumberOfCells()
                           for polydata in self.sensor_grids.data]

            if file_lengths != num_sensors:
                path_matches = {
                    data.file_paths[i]: file_lengths[i] == num_sensors[i] for i in
                    range(len(data.file_paths))
                }
                paths_to_report = [
                    path for path in path_matches if path_matches[path] is False]
                raise ValueError(
                    'File lengths must match grid sizes. Lengths of'
                    f' following files do not match grid size {tuple(paths_to_report)}.')

            return True

        # if object_name is other than grid check that length of data matches the length
        # of data in the model for that object.
        elif data.object_type in model_dataset_names[:-1]:

            # make sure the list of files is not empty
            if len(data.file_paths) == 0:
                raise ValueError(
                    f'For object with name {data.name} There are not file paths'
                    ' provided to load data from.'
                )

            # only one file is accepted
            elif len(data.file_paths) > 1:
                raise ValueError(
                    'Only one file path needs to be provided in order to load data on'
                    f' {data.object_type}. Multiple files are provided in the config'
                    ' file.'
                )

            # match length of file with the number of faces in the model
            if get_line_count(data.file_paths[0]) != len(
                    self.get_modeldataset_from_string(data.object_type).data):
                raise ValueError(
                    'The length of data in the file does not match the number of'
                    f' {data.object_type} objects in the model.'
                )
            return True

        else:
            raise ValueError(
                ' object_name must be from one of these'
                f' {model_dataset_names}. Instead got {data.object_type}.'
            )

    def _load_data(self, data: DataConfig) -> None:
        """Load validate data on a honeybee-vtk model.

        This is a helper method to the public load_config method.

        Args:
            data: A DataConfig object.
        """
        # if data is for a ModelDataSet grid
        if data.object_type == model_dataset_names[-1]:

            result = []
            for file_path in data.file_paths:
                res_file = pathlib.Path(file_path)
                grid_res = [float(v)
                            for v in res_file.read_text().splitlines()]
                result.append(grid_res)

        # if data is for a ModelDataSet other than grid
        elif data.object_type in model_dataset_names[:-1]:
            res_file = pathlib.Path(data.file_paths[0])
            result = [[float(v)] for v in res_file.read_text().splitlines()]

        ds = self.get_modeldataset_from_string(data.object_type)
        ds.add_data_fields(
            result, name=data.name, data_range=get_min_max(result))
        ds.color_by = data.name
        ds.display_mode = DisplayMode.SurfaceWithEdges

    def load_config(self, json_path: str) -> None:
        """Mount data on model from config json.

        Args:
            config: A dictionary returned by check_data_config
        """
        # Check if json is valid
        try:
            with open(json_path) as fh:
                config = json.load(fh)
        except json.decoder.JSONDecodeError:
            raise TypeError(
                'Not a valid json file.'
            )
        else:
            for json_obj in config.values():
                data = DataConfig.parse_obj(json_obj)
                if self._validate_data(data):
                    self._load_data(data)

    def update_display_mode(self, value: DisplayMode) -> None:
        """Change display mode for all the object types in the model.

        Sensor grids display model will not be affected. For changing the display model
        for a single object type, change the display_mode property separately.

        .. code-block:: python

            model.sensor_grids.display_mode = DisplayMode.Wireframe

        """
        for attr in DATA_SETS.values():
            self.__getattribute__(attr).display_mode = value

    def _convert_model(self, model: HBModel) -> None:
        """An internal method to convert the objects on class initiation."""

        for room in model.rooms:
            objects = convert_room(room)
            self._add_objects(self.separate_by_type(objects))

        for face in model.faces:
            objects = convert_face(face)
            self._add_objects(self.separate_by_type(objects))

        for face in model.orphaned_shades:
            self._shades.data.append(convert_shade(face))

        for face in model.orphaned_apertures:
            self._apertures.data.extend(convert_aperture(face))

        for face in model.orphaned_faces:
            objects = convert_face(face)
            self._add_objects(self.separate_by_type(objects))

    def _add_objects(self, data: Dict) -> None:
        """Add object to different fields based on data type.

        This method is called from inside ``_convert_model``. Valid values for key are
        different types:

            * aperture
            * door
            * shade
            * wall
            * floor
            * roof_ceiling
            * air_boundary
            * sensor_grid

        """
        for key, value in data.items():
            try:
                # Note: this approach will fail for air_boundary
                attr = DATA_SETS[key]
                self.__getattribute__(attr).data.extend(value)
            except KeyError:
                raise ValueError(f'Unsupported type: {key}')
            except AttributeError:
                raise AttributeError(f'Invalid attribute: {attr}')

    def to_vtkjs(self, folder: str = '.', name: str = None) -> str:
        """Write a vtkjs file.

        Write your honeybee-vtk model to a vtkjs file that you can open in
        Paraview-Glance.

        Args:
            folder: A valid text string representing the location of folder where
                you'd want to write the vtkjs file. Defaults to current working
                directory.
            name : Name for the vtkjs file. File name will be Model.vtkjs if not
                provided.

        Returns:
            A text string representing the file path to the vtkjs file.
        """

        # name of the vtkjs file
        file_name = name or 'model'
        # create a temp folder
        temp_folder = tempfile.mkdtemp()
        # The folder set by the user is the target folder
        target_folder = os.path.abspath(folder)
        # Set a file path to move the .zip file to the target folder
        target_vtkjs_file = os.path.join(target_folder, file_name + '.vtkjs')

        # write every dataset
        scene = []
        for data_set in DATA_SETS.values():
            data = getattr(self, data_set)
            path = data.to_folder(temp_folder)
            if not path:
                # empty dataset
                continue
            scene.append(data.as_data_set())

        # add sensor grids
        # it is separate from other DATA_SETS mainly for data visualization
        data = self.sensor_grids
        path = data.to_folder(temp_folder)
        if path:
            scene.append(data.as_data_set())

        # write index.json
        index_json = IndexJSON()
        index_json.scene = scene
        index_json.to_json(temp_folder)

        # zip as vtkjs
        temp_vtkjs_file = convert_directory_to_zip_file(temp_folder, extension='vtkjs',
                                                        move=False)

        # Move the generated vtkjs to target folder
        shutil.move(temp_vtkjs_file, target_vtkjs_file)

        return target_vtkjs_file

    def to_html(self, folder: str = '.', name: str = None, show: bool = False) -> str:
        """Write an HTML file.

        Write your honeybee-vtk model to an HTML file.

        Args:
            folder: A valid text string representing the location of folder where
                you'd want to write the HTML file. Defaults to current working directory.
            name : Name for the HTML file. File name will be Model.html if not provided.
            show: A boolean value. If set to True, the HTML file will be opened in the
                default browser. Defaults to False

        Returns:
            A text string representing the file path to the HTML file.
        """
        # Name of the html file
        file_name = name or 'model'
        # Set the target folder
        target_folder = os.path.abspath(folder)
        # Set a file path to move the .zip file to the target folder
        html_file = os.path.join(target_folder, file_name + '.html')
        # Set temp folder to do the operation
        temp_folder = tempfile.mkdtemp()
        vtkjs_file = self.to_vtkjs(temp_folder)
        temp_html_file = add_data_to_viewer(vtkjs_file)
        shutil.copy(temp_html_file, html_file)
        try:
            shutil.rmtree(temp_folder)
        except Exception:
            pass
        if show:
            webbrowser.open(html_file)
        return html_file

    @staticmethod
    def get_default_color(face_type: face_types) -> Color:
        """Get the default color based of face type.

        Use these colors to generate visualizations that are familiar for Ladybug Tools
        users. User can overwrite these colors as needed. This method converts decimal
        RGBA to integer RGBA values.
        """
        color = _COLORSET.get(face_type, [1, 1, 1, 1])
        return Color(*(v * 255 for v in color))

    @staticmethod
    def separate_by_type(data: List[PolyData]) -> Dict:
        """Separate PolyData objects by type."""
        data_dict = defaultdict(list)

        for d in data:
            data_dict[d.type].append(d)

        return data_dict
