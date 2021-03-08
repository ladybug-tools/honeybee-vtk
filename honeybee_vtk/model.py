"""A VTK representation of HBModel."""
from typing import Dict, List

from honeybee.model import Model as HBModel

from .types import PolyData
from .to_vtk import convert_face, convert_room, convert_shade, \
    convert_sensor_grid
from .helper import separate_by_type


class Model(object):

    def __init__(self, model: HBModel) -> None:
        super().__init__()
        self._model = model
        self._apertures = []  # apertures and orphaned apertures
        self._doors = []  # doors and orphaned doors
        self._shades = []  # shades and orphaned shades
        # face objects based on type
        self._walls = []
        self._floors = []
        self._roof_ceilings = []
        self._air_boundaries = []
        self._sensor_grids = []
        self._grid_loaded = False
        self._convert_model(model)

    @property
    def hb_model(self) -> HBModel:
        """Honeybee model that is used to build this model."""
        return self._model

    @property
    def model(self) -> List[PolyData]:
        """Model as a list of PolyData.

        The list doesn't include Radiance specific objects like sensor grids.
        """
        return self._walls + self._apertures + self._shades

    @property
    def walls(self) -> List[PolyData]:
        """Model walls."""
        return self._walls

    @property
    def apertures(self) -> List[PolyData]:
        """Model aperture."""
        return self._apertures

    @property
    def shades(self) -> List[PolyData]:
        """Model shades."""
        return self._shades

    def sensor_grids(self, load_type=0, force=False) -> List[PolyData]:
        """Model sensor grids."""
        if force or not self._grid_loaded:
            self._load_grids(self, load_type)
        return self._sensor_grids

    def _load_grids(self, grids_filter='*'):
        model = self.hb_model
        if hasattr(model.properties, 'radiance'):
            for sensor_grid in model.properties.radiance.sensor_grids:
                self._sensor_grids.append(convert_sensor_grid(sensor_grid))
        self._grid_loaded = True

    def _convert_model(self, model: HBModel) -> None:
        """An internal method to convert the objects on class initiation."""
        for room in model.rooms:
            objects = convert_room(room)
            self._add_objects(separate_by_type(objects))
        for face in model.faces:
            objects = convert_face(face)
            self._add_objects(separate_by_type(objects))
        for face in model.orphaned_shades:
            self._shade.append(convert_shade(face))

    def _add_objects(self, data: Dict) -> None:
        """Add object to different fields based on data type."""
        for key, value in data.items():
            try:
                self.__getattribute__(f'_{key.lower()}s').extend(value)
            except AttributeError:
                raise ValueError(f'Unsupported type: {key}')

    def to_vtkjs(self):
        raise NotImplementedError()
        # for layer_name in layer_names:
        #     # Set opacity for Apertures
        #     if layer_name == 'Aperture':
        #         opacity = 0.5
        #     else:
        #         opacity = 1

        #     template = copy.deepcopy(dataset_template)
        #     template['name'] = layer_name
        #     template['httpDataSetReader']['url'] = layer_name
        #     template['property']['diffuseColor'] = layer_colors[layer_name]
        #     template['property']['opacity'] = opacity

        #     datasets.append(template)

    def to_html(self):
        vtkjs_file = self.to_vtkjs()
        # convert_directory_to_zip_file(vtkjs_file)
        # add_data_to_viewer(vtkjs_file, html_path)
        # if show:
        #     webbrowser.open(target_html_file)
