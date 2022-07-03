"""A VTK representation of HBModel."""

from __future__ import annotations
import pathlib
import shutil
import webbrowser
import tempfile
import os
import json
import warnings

from collections import defaultdict
from typing import Dict, List, Union, Tuple

from honeybee.facetype import face_types
from honeybee.model import Model as HBModel
from honeybee_radiance.sensorgrid import SensorGrid
from honeybee_radiance.writer import _filter_by_pattern
from ladybug.color import Color
from ladybug_geometry.geometry3d import Mesh3D

from .actor import Actor
from .scene import Scene
from .camera import Camera
from .types import ModelDataSet, PolyData, RadialSensor
from .to_vtk import convert_aperture, convert_face, convert_room, convert_shade, \
    convert_sensor_grid, convert_door
from .vtkjs.schema import IndexJSON, DisplayMode, SensorGridOptions
from .vtkjs.helper import convert_directory_to_zip_file, add_data_to_viewer
from .types import DataSetNames, VTKWriters, JoinedPolyData, ImageTypes
from .config import DataConfig, Autocalculate
from .legend_parameter import Text
from .text_actor import TextActor


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
            self, hb_model: HBModel,
            grid_options: SensorGridOptions = SensorGridOptions.Ignore,
            radial_sensor: RadialSensor = RadialSensor()) -> None:
        """Instantiate a honeybee-vtk model object.

        Args:
            model : A text string representing the path to the hbjson file.
            load_grids: A SensorGridOptions object. Defaults to SensorGridOptions.Ignore
                which will ignore the grids in hbjson and will not load them in the
                honeybee-vtk model.
            radial_sensor: A RadialSensor object to customize the triangles to be 
                created in the radial sensor grid in case the radial grid is selected
                from the sensor grid options.
        """
        super().__init__()

        self._hb_model = hb_model
        self._sensor_grids_option = grid_options
        self._apertures = ModelDataSet('Aperture',
                                       color=self.get_default_color('Aperture'))
        self._doors = ModelDataSet('Door', color=self.get_default_color('Door'))
        self._shades = ModelDataSet('Shade', color=self.get_default_color('Shade'))
        self._walls = ModelDataSet('Wall', color=self.get_default_color('Wall'))
        self._floors = ModelDataSet('Floor', color=self.get_default_color('Floor'))
        self._roof_ceilings = ModelDataSet('RoofCeiling',
                                           color=self.get_default_color('RoofCeiling'))
        self._air_boundaries = ModelDataSet('AirBoundary',
                                            color=self.get_default_color('AirBoundary'))
        self._sensor_grids = ModelDataSet('Grid', color=self.get_default_color('Grid'))
        self._cameras = []
        self._radial_sensor = radial_sensor
        self._convert_model()
        self._load_grids()
        self._load_cameras()

    @classmethod
    def from_hbjson(cls, hbjson: str,
                    load_grids: SensorGridOptions = SensorGridOptions.Ignore,
                    radial_sensor: RadialSensor = RadialSensor()) -> Model:
        """Translate hbjson to a honeybee-vtk model.

        Args:
            model : A text string representing the path to the hbjson file.
            load_grids: A SensorGridOptions object. Defaults to SensorGridOptions.Ignore
                which will ignore the grids in hbjson and will not load them in the
                honeybee-vtk model.
            radial_sensor: A RadialSensor object to customize the triangles to be 
                created in the radial sensor grid in case the radial grid is selected
                from the sensor grid options.

        Returns:
            A honeybee-vtk model object.
        """
        hb_file = pathlib.Path(hbjson)
        assert hb_file.is_file(), f'{hbjson} doesn\'t exist.'
        model = HBModel.from_hbjson(hb_file.as_posix())
        return cls(model, load_grids, radial_sensor)

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

    @cameras.setter
    def cameras(self, cams: List(Camera)) -> None:
        """Set the cameras for this Model object."""
        self._cameras = cams

    def get_modeldataset(self, dataset: DataSetNames) -> ModelDataSet:
        """Get a ModelDataSet object from a model.

        Args:
            dataset: A DataSetNames object.

        Returns:
            A ModelDataSet object.
        """
        ds = {ds.name.lower(): ds for ds in self}
        return ds[dataset.value]

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

    def _load_grids(self) -> None:
        """Load sensor grids."""
        if self._sensor_grids_option == SensorGridOptions.Ignore:
            return
        if hasattr(self._hb_model.properties, 'radiance') and \
                self._hb_model.properties.radiance.sensor_grids:

            grids = self._hb_model.properties.radiance.sensor_grids

            # list of unique sensor_grid identifiers in the model
            ids = set([grid.identifier for grid in grids])

            # if all the grids have the same identifier, merge them into one grid
            if len(ids) == 1:
                id = grids[0].identifier

                # if it's just one grid, use it
                if len(grids) == 1:
                    sensor_grid = grids[0]
                # if there are more than one grid, merge them first
                else:
                    grid_meshes = [grid.mesh for grid in grids]
                    if all(grid_meshes):
                        mesh = Mesh3D.join_meshes(grid_meshes)
                        sensor_grid = SensorGrid.from_mesh3d(id, mesh)
                    else:
                        sensors = [sensor for grid in grids for sensor
                                   in grid.sensors]
                        sensor_grid = SensorGrid(id, sensors)

                # TODO extract this to a function
                try:
                    convert_sensor_grid(sensor_grid, self._sensor_grids_option,
                                        self._radial_sensor.angle, 
                                        self._radial_sensor.radius)
                except ValueError:
                    warnings.warn(f'Grid {id} does not have mesh information. Hence, '
                                  'it will not be converted to a sensor grid. Try with'
                                  ' SensorGridOptions.Sensors.')
                else:
                    self._sensor_grids.data.append(convert_sensor_grid(
                        sensor_grid, self._sensor_grids_option, self._radial_sensor.angle,
                        self._radial_sensor.radius))
            # else add them as separate grids
            else:
                for sensor_grid in grids:
                    # TODO extract this to a function
                    try:
                        convert_sensor_grid(sensor_grid, self._sensor_grids_option,
                                            self._radial_sensor.angle,
                                            self._radial_sensor.radius)
                    except ValueError:
                        warnings.warn(f'Grid {sensor_grid.identifier} does not have'
                                      ' mesh information. Hence, it will not be'
                                      ' converted to a sensor grid. Try with'
                                      ' SensorGridOptions.Sensors.')
                    else:
                        self._sensor_grids.data.append(convert_sensor_grid(
                            sensor_grid, self._sensor_grids_option,
                            self._radial_sensor.angle, self._radial_sensor.radius))

    def _load_cameras(self) -> None:
        """Load radiance views."""
        if len(self._hb_model.properties.radiance.views) > 0:
            for view in self._hb_model.properties.radiance.views:
                self._cameras.append(Camera.from_view(view))

    def update_display_mode(self, value: DisplayMode) -> None:
        """Change display mode for all the object types in the model.

        Sensor grids display model will not be affected. For changing the display model
        for a single object type, change the display_mode property separately.

        .. code-block:: python

            model.sensor_grids.display_mode = DisplayMode.Wireframe

        """
        for attr in DATA_SETS.values():
            self.__getattribute__(attr).display_mode = value

    def _convert_model(self) -> None:
        """An internal method to convert the objects on class initiation."""

        if hasattr(self._hb_model, 'rooms'):
            for room in self._hb_model.rooms:
                objects = convert_room(room)
                self._add_objects(self.separate_by_type(objects))

        if hasattr(self._hb_model, 'orphaned_shades'):
            for face in self._hb_model.orphaned_shades:
                self._shades.data.append(convert_shade(face))

        if hasattr(self._hb_model, 'orphaned_apertures'):
            for face in self._hb_model.orphaned_apertures:
                self._apertures.data.extend(convert_aperture(face))

        if hasattr(self._hb_model, 'orphaned_doors'):
            for face in self._hb_model.orphaned_doors:
                self._doors.data.extend(convert_door(face))

        if hasattr(self._hb_model, 'orphaned_faces'):
            for face in self._hb_model.orphaned_faces:
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

    def actors(self) -> List[Actor]:
        """Create a list of vtk actors from a honeybee-vtk model.

        Args:
            model: A honeybee-vtk model.

        Returns:
            A list of vtk actors.
        """
        return [Actor(modeldataset=ds) for ds in self if len(ds.data) > 0]

    def to_vtkjs(self, *, folder: str = '.', name: str = None, config: str = None,
                 validation: bool = False,
                 model_display_mode: DisplayMode = DisplayMode.Shaded,
                 grid_display_mode: DisplayMode = DisplayMode.Shaded) -> str:
        """Write the model to a vtkjs file.

        Write your honeybee-vtk model to a vtkjs file that you can open in
        Paraview-Glance or the Pollination Viewer.

        Args:
            folder: A valid text string representing the location of folder where
                you'd want to write the vtkjs file. Defaults to current working
                directory.
            name : Name for the vtkjs file. File name will be Model.vtkjs if not
                provided.
            config: Path to the config file in JSON format. Defaults to None.
            validation: Boolean to indicate whether to validate the data before loading.
                Defaults to False.
            model_display_mode: Display mode for the model. Defaults to shaded.
            grid_display_mode: Display mode for the Grids. Defaults to shaded.

        Returns:
            A text string representing the file path to the vtkjs file.
        """
        scene = Scene()
        actors = self.actors()
        scene.add_actors(actors)

        self.update_display_mode(model_display_mode)
        self.sensor_grids.display_mode = grid_display_mode

        # load data if provided
        if config:
            self.load_config(config, scene=scene, validation=validation, legend=True)

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

        try:
            shutil.rmtree(temp_folder)
        except Exception:
            pass

        return target_vtkjs_file

    def to_html(self, *, folder: str = '.', name: str = None, show: bool = False,
                config: str = None,
                validation: bool = False,
                model_display_mode: DisplayMode = DisplayMode.Shaded,
                grid_display_mode: DisplayMode = DisplayMode.Shaded) -> str:
        """Write the model to an HTML file.

        Write your honeybee-vtk model to an HTML file that you can open in any modern
        browser and can also share with other.

        Args:
            folder: A valid text string representing the location of folder where
                you'd want to write the HTML file. Defaults to current working directory.
            name : Name for the HTML file. File name will be Model.html if not provided.
            show: A boolean value. If set to True, the HTML file will be opened in the
                default browser. Defaults to False
            config: Path to the config file in JSON format. Defaults to None.
            validation: Boolean to indicate whether to validate the data before loading.
            model_display_mode: Display mode for the model. Defaults to shaded.
            grid_display_mode: Display mode for the Grids. Defaults to shaded.

        Returns:
            A text string representing the file path to the HTML file.
        """
        self.update_display_mode(model_display_mode)
        # Name of the html file
        file_name = name or 'model'
        # Set the target folder
        target_folder = os.path.abspath(folder)
        # Set a file path to move the .html file to the target folder
        html_file = os.path.join(target_folder, file_name + '.html')
        # Set temp folder to do the operation
        temp_folder = tempfile.mkdtemp()
        vtkjs_file = self.to_vtkjs(
            folder=temp_folder, config=config, validation=validation,
            model_display_mode=model_display_mode, grid_display_mode=grid_display_mode)
        temp_html_file = add_data_to_viewer(vtkjs_file)
        shutil.copy(temp_html_file, html_file)
        try:
            shutil.rmtree(temp_folder)
        except Exception:
            pass
        if show:
            webbrowser.open(html_file)
        return html_file

    def to_files(self, *, folder: str = '.', name: str = None,
                 writer: VTKWriters = VTKWriters.binary, config: str = None,
                 validation: bool = False,
                 model_display_mode: DisplayMode = DisplayMode.Shaded,
                 grid_display_mode: DisplayMode = DisplayMode.Shaded) -> str:
        """
        Write a .zip of VTK/VTP files.

        Args:
            folder: File path to the output folder. The file
                will be written to the current folder if not provided.
            name: A text string for the name of the .zip file to be written. If no
                text string is provided, the name of the HBJSON file will be used as a
                file name for the .zip file.
            writer: A VTkWriters object. Default is binary which will write .vtp files.
            config: Path to the config file in JSON format. Defaults to None.
            validation: Boolean to indicate whether to validate the data before loading.
            model_display_mode: Display mode for the model. Defaults to shaded.
            grid_display_mode: Display mode for the Grids. Defaults to shaded.

        Returns:
            A text string containing the path to the .zip file with VTK/VTP files.
        """
        scene = Scene()
        actors = self.actors()
        scene.add_actors(actors)

        self.update_display_mode(model_display_mode)
        self.sensor_grids.display_mode = grid_display_mode

        # load data if provided
        if config:
            self.load_config(config, scene=scene, validation=validation, legend=True)

        # Name of the html file
        file_name = name or 'model'
        # Set the target folder
        target_folder = os.path.abspath(folder)
        # Set a file path to move the .zip file to the target folder
        target_zip_file = os.path.join(target_folder, file_name + '.zip')
        # Set temp folder to do the operation
        temp_folder = tempfile.mkdtemp()
        # Write datasets to vtk/vtp files
        for ds in self:
            if len(ds.data) == 0:
                continue

            elif len(ds.data) > 1:
                jp = JoinedPolyData()
                jp.extend(ds.data)
                jp.to_vtk(temp_folder, ds.name, writer)

            elif len(ds.data) == 1:
                polydata = ds.data[0]
                polydata.to_vtk(temp_folder, ds.name, writer)

        # collect files in a zip
        temp_zip_file = convert_directory_to_zip_file(temp_folder, extension='zip',
                                                      move=False)
        # Move the generated zip file to the target folder
        shutil.move(temp_zip_file, target_zip_file)

        try:
            shutil.rmtree(temp_folder)
        except Exception:
            pass

        return target_zip_file

    def to_images(self, *, folder: str = '.', config: str = None,
                  validation: bool = False,
                  model_display_mode: DisplayMode = DisplayMode.Shaded,
                  grid_display_mode: DisplayMode = DisplayMode.Shaded,
                  background_color: Tuple[int, int, int] = None,
                  view: List[str] = None,
                  image_type: ImageTypes = ImageTypes.png,
                  image_width: int = 0, image_height: int = 0) -> List[str]:
        """Export images from model.

        Args:
            folder: A valid text string representing the location of folder where
                you'd want to write the images. Defaults to current working directory.
            config: Path to the config file in JSON format. Defaults to None.
            validation: Boolean to indicate whether to validate the data before loading.
            model_display_mode: Display mode for the model. Defaults to shaded.
            grid_display_mode: Display mode for the grid. Defaults to shaded.
            background_color: Background color of the image. Defaults to white.
            view: A list of paths to radiance view files. Defaults to None.
            image_type: Image type to be exported. Defaults to png.
            image_width: Image width. Defaults to 0. Which will use the default radiance
                view's horizontal angle.
            image_height: Image height. Defaults to 0. Which will use the default radiance
                view's vertical angle.

        Returns:
            A list of text strings representing the file paths to the images.
        """
        scene = Scene(background_color=background_color)
        actors = self.actors()
        scene.add_actors(actors)

        self.update_display_mode(model_display_mode)
        self.sensor_grids.display_mode = grid_display_mode

        if config:
            self.load_config(config, scene=scene, legend=True, validation=validation)

        # Set a default camera if there are no cameras in the model
        if not self.cameras and not view:
            camera = Camera(identifier='plan', projection='l')
            scene.add_cameras(camera)
            bounds = Actor.get_bounds(actors)
            centroid = Actor.get_centroid(actors)
            aerial_cameras = camera.aerial_cameras(bounds, centroid)
            scene.add_cameras(aerial_cameras)

        else:
            if len(self.cameras) != 0:
                cameras = self.cameras
                scene.add_cameras(cameras)

            if view:
                for vf in view:
                    camera = Camera.from_view_file(file_path=vf)
                    scene.add_cameras(camera)

        for actor in scene.actors:
            if actor.name == 'Grid':
                assert actor.modeldataset.display_mode == grid_display_mode, 'Grid display'\
                    ' mode is not set correctly.'
            else:
                assert actor.modeldataset.display_mode == model_display_mode, 'Model display'\
                    ' mode is not set correctly.'

        return scene.export_images(
            folder=folder, image_type=image_type,
            image_width=image_width, image_height=image_height)

    def to_grid_images(self, config: str, *, folder: str = '.',
                       grid_filter: Union[str, List[str]] = '*',
                       full_match: bool = False,
                       grid_display_mode: DisplayMode = DisplayMode.SurfaceWithEdges,
                       background_color: Tuple[int, int, int] = None,
                       image_type: ImageTypes = ImageTypes.png,
                       image_width: int = 0, image_height: int = 0, image_name: str = '',
                       text_actor: TextActor = None,
                       grid_camera_dict: Dict[str, vtk.vtkCamera] = None,
                       extract_camera: bool = False,
                       grid_colors: List[Color] = None,
                       sub_folder_name: str = None) -> Union[Dict[str, Camera],
                                                             List[str]]:
        """Export am image for each grid in the model.

        Use the config file to specify which grids with which data to export. For
        instance, if the config file has DataConfig objects for 'DA' and 'UDI', and
        'DA' is kept hidden, then all grids with 'UDI' data will be exported.
        Additionally, images from a selected number of grids can be exported by
        using the by specifying the identifiers of the grids to export in the
        grid_filter object in the config file.

        Note that the parameters grid_camera_dict and extract_camera are mutually
        exclusive. If both are provided, the extract_camera will be used and the
        grid_camera_dict will be ignored.

        Args:
            config: Path to the config file in JSON format.
            folder: Path to the folder where you'd like to export the images. Defaults to
                    the current working directory.
            grid_filter: A list of grid identifiers or a regex pattern as a string to
                filter the grids. Defaults to None.
            full_match: A boolean to filter grids by their identifiers as full matches.
                Defaults to False.
            display_mode: Display mode for the grid. Defaults to surface with edges.
            background_color: Background color of the image. Defaults to white.
            image_type: Image type to be exported. Defaults to png.
            image_width: Image width in pixels. Defaults to 0. Which will use the
                default radiance view's horizontal angle to derive the width.
            image_height: Image height in pixels. Defaults to 0. Which will use the
                default radiance view's vertical angle to derive the height.
            image_name: A text string that sets the name of the image. Defaults to ''.
            text_actor: A TextActor object that defines the properties of the text to be
                added to the image. Defaults to None.
            grid_camera_dict: A dictionary of grid identifiers and vtkCamera objects.
                If provided, the camera objects specified in the dict will be used to
                export the images. This is useful when a camera from another run is
                to be used in this run to export an image. Defaults to None.
            extract_camera: Boolean to indicate whether to extract the camera from the
                for this run to use for the next run. Defaults to False.
            sub_folder_name: A text string that sets the name of the subfolder where
                the images will be exported. This is useful when the images are to be
                exported for multiple time periods such as whole day of June 21, and
                the whole day of March, 21. Defaults to None.

        Returns:
            Path to the folder where the images are exported for each grid. Or a
            dictionary of grid identifiers and camera objects.
        """
        assert len(self.sensor_grids.data) != 0, 'No sensor grids found in the model.'

        if self._sensor_grids_option == SensorGridOptions.Sensors:
            grid_display_mode = DisplayMode.Points

        config_data = self.load_config(config)

        grid_polydata_lst = _filter_grid_polydata(
            self.sensor_grids.data, self._hb_model, grid_filter, full_match)

        output: Union[Dict[str, Camera], List[str]] = {} if extract_camera else []

        grid_colors_supplied = True if grid_colors else False
        for data in config_data:
            for grid_polydata in grid_polydata_lst:
                dataset = ModelDataSet(name=grid_polydata.identifier,
                                       data=[grid_polydata],
                                       display_mode=grid_display_mode)

                if not grid_colors_supplied and data.grid_colors:
                    grid_colors = [Color(r, g, b) for r, g, b in data.grid_colors]

                dataset.color_by = data.identifier

                if grid_colors:
                    if len(grid_colors) == 1:
                        dataset.active_field_info.legend_parameter._assign_colors(
                            [Color(255, 255, 255), grid_colors[0]])
                    else:
                        dataset.active_field_info.legend_parameter._assign_colors(
                            grid_colors)

                actor = Actor(dataset)
                camera = _camera_to_grid_actor(actor, data.identifier)
                scene = Scene(background_color=background_color, actors=[actor],
                              cameras=[camera],
                              text_actor=text_actor)
                legend_range = self._get_legend_range(data)
                self._load_legend_parameters(data, scene, legend_range)

                if extract_camera:
                    vtk_camera = None
                    output[grid_polydata.identifier] = scene.export_images(
                        folder=folder, image_type=image_type, image_width=image_width,
                        image_height=image_height, image_name=image_name,
                        vtk_camera=vtk_camera, extract_camera=extract_camera
                    )
                else:
                    if grid_camera_dict:
                        vtk_camera = grid_camera_dict[grid_polydata.identifier]
                    else:
                        vtk_camera = None

                    # this is not a good design but it takes too much refactoring to
                    # remove it. I'm writing this down for whenever we get a chance
                    # to refactor honeybee-vtk.
                    if not sub_folder_name:
                        grid_folder = pathlib.Path(
                            f'{folder}/{grid_polydata.identifier}')
                    else:
                        grid_folder = pathlib.Path(
                            f'{folder}/{grid_polydata.identifier}/{sub_folder_name}')

                    if not grid_folder.exists():
                        grid_folder.mkdir(parents=True, exist_ok=True)

                    output += scene.export_images(folder=grid_folder,
                                                  image_type=image_type,
                                                  image_width=image_width,
                                                  image_height=image_height,
                                                  image_name=image_name,
                                                  vtk_camera=vtk_camera)

        return output

    @ staticmethod
    def get_default_color(face_type: face_types) -> Color:
        """Get the default color based of face type.

        Use these colors to generate visualizations that are familiar for Ladybug Tools
        users. User can overwrite these colors as needed. This method converts decimal
        RGBA to integer RGBA values.
        """
        color = _COLORSET.get(face_type, [1, 1, 1, 1])
        return Color(*(v * 255 for v in color))

    @ staticmethod
    def separate_by_type(data: List[PolyData]) -> Dict:
        """Separate PolyData objects by type."""
        data_dict = defaultdict(list)

        for d in data:
            data_dict[d.type].append(d)

        return data_dict

    def load_config(self, json_path: str, scene: Scene = None,
                    validation: bool = False, legend: bool = False) -> List[DataConfig]:
        """Mount data on model from config json.

        Args:
            json_path: File path to the config json file.
            scene: A honeybee-vtk scene object. Defaults to None.
            validation: A boolean indicating whether to validate the data before loading.
            legend: A boolean indicating whether to load legend parameters.

        Returns:
            A list of parsed DataConfig objects.
        """
        assert len(self.sensor_grids.data) > 0, 'Sensor grids are not loaded on'
        ' this model. Reload them using grid options.'

        config_dir = pathlib.Path(json_path).parent
        config_data: List[DataConfig] = []

        try:
            with open(json_path) as fh:
                config = json.load(fh)
        except json.decoder.JSONDecodeError:
            raise TypeError(
                'Not a valid json file.'
            )
        else:
            for json_obj in config['data']:
                # validate config
                data = DataConfig.parse_obj(json_obj)
                # only if data is requested move forward.
                if not data.hide:
                    folder_path = pathlib.Path(data.path)
                    if not folder_path.is_dir():
                        folder_path = config_dir.joinpath(
                            folder_path).resolve().absolute()
                        data.path = folder_path.as_posix()
                        if not folder_path.is_dir():
                            raise FileNotFoundError(
                                f'No folder found at {data.path}')
                    grid_type = self._get_grid_type()
                    # Validate data if asked for
                    if validation:
                        self._validate_simulation_data(data, grid_type)
                    # get legend range if provided by the user
                    legend_range = self._get_legend_range(data)
                    # Load data
                    self._load_data(data, grid_type, legend_range)
                    # Load legend parameters
                    if legend:
                        self._load_legend_parameters(data, scene, legend_range)
                    config_data.append(data)
                else:
                    warnings.warn(
                        f'Data for {data.identifier} is not loaded.'
                    )
            return config_data

    def _get_grid_type(self) -> str:
        """Get the type of grid in the model

        Args:
            model(Model): A honeybee-vtk model.

        Returns:
            A string indicating whether the model has points and meshes.
        """

        if self.sensor_grids.data[0].GetNumberOfCells() == 1:
            return 'points'
        else:
            return 'meshes'

    def _validate_simulation_data(self, data: DataConfig, grid_type: str) -> None:
        """Match result data with the sensor grids in the model.

        It will be checked if the number of data files and the names of the
        data files match with the grid identifiers. This function does not support
        validating result data for other than sensor grids as of now.

        This is a helper method to the public load_config method.

        Args:
            data: A DataConfig object.
            grid_type: A string indicating whether the model has points and meshes.
        """
        # file path to the json file
        grids_info_json = pathlib.Path(data.path).joinpath('grids_info.json')

        # read the json file
        with open(grids_info_json) as fh:
            grids_info = json.load(fh)

        # TODO: Make sure to remove this limitation. A user should not have to always
        # TODO: load all the grids
        assert len(self.sensor_grids.data) == len(grids_info), 'The number of result'\
            f' files {len(grids_info)} does for {data.identifier} does not match'\
            f' the number of sensor grids in the model {len(self.sensor_grids.data)}.'

        # match identifiers of the grids with the identifiers of the result files
        grids_model_identifiers = [grid.identifier for grid in self.sensor_grids.data]
        grids_info_identifiers = [grid['identifier'] for grid in grids_info]
        assert grids_model_identifiers == grids_info_identifiers, 'The identifiers of'\
            ' the sensor grids in the model do not match the identifiers of the grids'\
            f' in the grids_info.json for {data.identifier}.'

        # make sure length of each file matches the number of sensors in grid
        file_lengths = [grid['count'] for grid in grids_info]

        # check if the grid data is meshes or points
        # if grid is sensors
        if grid_type == 'points':
            num_sensors = [polydata.GetNumberOfPoints()
                           for polydata in self.sensor_grids.data]
        # if grid is meshes
        else:
            num_sensors = [polydata.GetNumberOfCells()
                           for polydata in self.sensor_grids.data]

        # lastly check if the length of a file matches the number of sensors or
        # meshes on grid
        if file_lengths != num_sensors:
            length_matching = {
                grids_info_identifiers[i]: file_lengths[i] == num_sensors[i] for i in
                range(len(grids_model_identifiers))
            }
            names_to_report = [
                id for id in length_matching if length_matching[id] is False]
            raise ValueError(
                'File lengths of result files must match the number of sensors on grids.'
                ' Lengths of files with following names do not match'
                f' {tuple(names_to_report)}.')

    def _load_data(self, data: DataConfig, grid_type: str,
                   legend_range: List[Union[float, int]]) -> None:
        """Load validated data on a honeybee-vtk model.

        This is a helper method to the public load_config method.

        Args:
            data (DataConfig): A Dataconfig object.
            model: A honeybee-vtk model.
            grid_type: A string indicating whether the sensor grid in the model is
                made of points or meshes.
            legend_range: A list of min and max values of the legend parameters
                provided by the user in the config file.
        """
        folder_path = pathlib.Path(data.path)
        folder_path = folder_path.as_posix()
        folder_path = pathlib.Path(folder_path)

        identifier = data.identifier
        if isinstance(data.lower_threshold, float):
            lower_threshold = data.lower_threshold
        else:
            lower_threshold = None
        if isinstance(data.upper_threshold, float):
            upper_threshold = data.upper_threshold
        else:
            upper_threshold = None

        result_file_paths = _get_result_file_paths(folder_path)
        result = []
        for res_file_path in result_file_paths:
            assert res_file_path.exists(), f'No file found at {res_file_path}'
            grid_res = [float(v)
                        for v in res_file_path.read_text().splitlines()]
            result.append(grid_res)

        ds = self.get_modeldataset(DataSetNames.grid)

        if grid_type == 'meshes':
            ds.add_data_fields(result, name=identifier, per_face=True,
                               data_range=legend_range, lower_threshold=lower_threshold,
                               upper_threshold=upper_threshold)
            ds.color_by = identifier
        else:
            ds.add_data_fields(result, name=identifier, per_face=False,
                               data_range=legend_range, lower_threshold=lower_threshold,
                               upper_threshold=upper_threshold)
            ds.color_by = identifier

    @ staticmethod
    def _get_legend_range(data: DataConfig) -> List[Union[float, int]]:
        """Read and get legend min and max values from data if provided by the user.

        The value provided by this function is processed and validated in _get_data_range
        function in the type module.

        Args:
            data (DataConfig): A Dataconfig object.

        Returns:
            A list of two numbers representing min and max values for data.
        """
        if data.legend_parameters:
            legend_params = data.legend_parameters

            if isinstance(legend_params.min, Autocalculate):
                min = None
            else:
                min = legend_params.min

            if isinstance(legend_params.max, Autocalculate):
                max = None
            else:
                max = legend_params.max

            return [min, max]

    def _load_legend_parameters(self, data: DataConfig, scene: Scene,
                                legend_range: List[Union[float, int]]) -> None:
        """Load legend_parameters.

        Args:
            data: A Dataconfig object.
            scene: A honeyebee-vtk scene object.
            legend_range: A list of min and max values of the legend parameters provided by
                the user in the config file.
        """

        legend_params = data.legend_parameters
        legend = scene.legend_parameter(data.identifier)
        legend.colorset = legend_params.color_set
        legend.reverse_colorset = legend_params.reverse_color_set

        legend.unit = data.unit
        if legend_range:
            legend.min, legend.max = legend_range
        else:
            legend.min, legend.max = [None, None]
        legend.hide_legend = legend_params.hide_legend
        legend.orientation = legend_params.orientation
        legend.position = legend_params.position

        legend.width = legend_params.width
        legend.height = legend_params.height

        if isinstance(legend_params.color_count, int):
            legend.color_count = legend_params.color_count
        else:
            legend.color_count = None

        if isinstance(legend_params.label_count, int):
            legend.label_count = legend_params.label_count
        else:
            legend.label_count = None

        legend.decimal_count = legend_params.decimal_count
        legend.preceding_labels = legend_params.preceding_labels

        label_params = legend_params.label_parameters
        legend.label_parameters = Text(
            label_params.color, label_params.size, label_params.bold)

        title_params = legend_params.title_parameters
        legend.title_parameters = Text(
            title_params.color, title_params.size, title_params.bold)


def _camera_to_grid_actor(actor: Actor, data_name: str, zoom: int = 2,
                          auto_zoom: bool = True, camera_offset: int = 3,
                          clipping_range: Tuple[int, int] = (0, 4), ) -> Camera:
    """Create a Camera for a grid actor.

    This function uses the center point of a grid actor to create a camera that is
    setup at the camera_offset distance from the center point.

    Args:
        actor: An Actor object.
        data_name: name of the data being loaded on the grid. This is
            used in naming the image files.
        zoom: The zoom level of the camera. Defaults to 2.
        auto_zoom: A boolean to set the camera to auto zoom. Setting this to True will
            discard the Zoom level. Set this to False to use the zoom level. Defaults to
            True.
        camera_offset: The distance between the camera and the sensor grid.
            Defaults to 100.
        clipping_range: The clipping range of the camera. Defaults to (100, 101).

    Returns:
        A Camera object.
    """
    cent_pt = actor.centroid
    return Camera(identifier=f'{data_name}_{actor.name}',
                  position=(cent_pt.x, cent_pt.y, cent_pt.z + camera_offset),
                  projection='l',
                  focal_point=cent_pt,
                  clipping_range=clipping_range,
                  parallel_scale=zoom,
                  reset_camera=auto_zoom)


def _get_result_file_paths(folder_path: Union[str, pathlib.Path]):

    if not isinstance(folder_path, pathlib.Path):
        folder_path = pathlib.Path(folder_path)

    grids_info_json = folder_path.joinpath('grids_info.json')
    with open(grids_info_json) as fh:
        grids_info = json.load(fh)

    # finding file extension for grid results
    # This could have been avoided if the file extension was provided in the
    # grids_info.json file.
    extension = None
    match = pathlib.Path(grids_info[0]['full_id']).stem
    for path in folder_path.rglob('*'):
        if path.stem == match:
            extension = path.suffix
            break
    else:
        raise ValueError(f'Failed to find the extension from {path}')

    # result file paths
    return [folder_path.joinpath(f"{grid['full_id']}{extension}")
            for grid in grids_info]


def _filter_grid_polydata(grid_polydata_lst: List[PolyData], model: HBModel,
                          grid_filter: Union[str, List[str]],
                          full_match) -> List[PolyData]:
    """Filter grid polydata based on sensor grids.

    Args:
        grid_polydata_lst: A list of grid polydata objects.
        model: A honeybee model object.
        grid_filter: A list of grid identifiers or a regex pattern as a string to filter
            the grid polydata.
        full_match: A boolean to filter grids by their identifiers as full matches.

    Returns:
        A list of PolyData objects for Grids.
    """
    if not grid_filter or grid_filter[0] == '*':
        return grid_polydata_lst
    else:
        filtered_sensor_grids = _filter_by_pattern(
            model.properties.radiance.sensor_grids, grid_filter, full_match)
        sensorgrid_identifiers = [
            grid.identifier for grid in filtered_sensor_grids]
        filtered_grid_polydata_lst = [grid for grid in grid_polydata_lst
                                      if grid.name in sensorgrid_identifiers]
        if not filtered_grid_polydata_lst:
            raise ValueError('No grids found in the model that match the'
                             f' filter {grid_filter}.')
        return filtered_grid_polydata_lst
