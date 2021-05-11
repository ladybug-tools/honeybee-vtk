"""Functions to translate HB Model objects to PolyData or JoinedPolyData.

honeybee-vtk provides a wrapper for vtkPolyData or vtkAppendPolyData which are used
instead of the original objects to add additional fields that are needed to provide
additional functionalities in honeybee-vtk. See ``types`` module for more information.

There are two sets of functions in this module:

    - create_x : These methods create an object from other objects. For instance
        create_polyline creates a polyline for a list of points.
    - convert_x: These methods convert a LBT object directly to a PolyData. For instance
        convert_polyline converts a Polyline3D to a VTK-based Polyline.

"""

from typing import List

import vtk

from ladybug_geometry.geometry3d import Face3D, Mesh3D, Point3D, Vector3D, Polyline3D
from honeybee.room import Room
from honeybee.face import Face
from honeybee.aperture import Aperture
from honeybee.shade import Shade
from honeybee_radiance.sensorgrid import SensorGrid

from .types import PolyData, JoinedPolyData
from .vtkjs.schema import SensorGridOptions


def convert_face_3d(face: Face3D) -> PolyData:
    """Convert a ladybug_geometry.Face3D to vtkPolyData."""
    # check if geometry has holes or is convex
    # mesh them and use convert_mesh
    if face.has_holes or not face.is_convex:
        return convert_mesh(face.triangulated_mesh3d)

    # create a PolyData from face points
    points = vtk.vtkPoints()
    polygon = vtk.vtkPolygon()
    cells = vtk.vtkCellArray()

    vertices_count = len(face.vertices)
    polygon.GetPointIds().SetNumberOfIds(vertices_count)
    for ver in face.vertices:
        points.InsertNextPoint(*ver)
    for count in range(vertices_count):
        polygon.GetPointIds().SetId(count, count)
    cells.InsertNextCell(polygon)

    face_vtk = PolyData()
    face_vtk.SetPoints(points)
    face_vtk.SetPolys(cells)

    return face_vtk


def convert_mesh(mesh: Mesh3D) -> PolyData:
    """Convert a ladybug_geometry.Mesh to vtkPolyData."""
    points = vtk.vtkPoints()
    polygon = vtk.vtkPolygon()
    cells = vtk.vtkCellArray()

    for ver in mesh.vertices:
        points.InsertNextPoint(*ver)

    for face in mesh.faces:
        polygon.GetPointIds().SetNumberOfIds(len(face))
        for count, i in enumerate(face):
            polygon.GetPointIds().SetId(count, i)
        cells.InsertNextCell(polygon)

    grid_vtk = PolyData()
    grid_vtk.SetPoints(points)
    grid_vtk.SetPolys(cells)

    return grid_vtk


def convert_sensor_grid(
    sensor_grid: SensorGrid, load_option: SensorGridOptions = SensorGridOptions.Mesh
        ) -> PolyData:
    """Convert a honeybee-radiance sensor grid to a vtkPolyData."""
    if load_option == SensorGridOptions.Sensors:
        # load sensors
        points = [ap.pos for ap in sensor_grid.sensors]
        grid_data = convert_points(points)
    else:
        mesh = sensor_grid.mesh
        if mesh is None:
            raise ValueError(
                f'{sensor_grid.display_name} does not include mesh information. '
                'Try again with SensorGridOptions.Sensors'
                )
        grid_data = convert_mesh(sensor_grid.mesh)

    grid_data.identifier = sensor_grid.identifier
    grid_data.display_name = sensor_grid.display_name
    grid_data.type = 'Grid'
    return grid_data


def convert_shade(shade: Shade) -> PolyData:
    shade_data = convert_face_3d(shade.geometry)
    shade_data.identifier = shade.identifier
    shade_data.display_name = shade.display_name
    shade_data.type = 'Shade'
    return shade_data


def convert_aperture(aperture: Aperture) -> List[PolyData]:
    aperture_data = convert_face_3d(aperture.geometry)
    aperture_data.type = 'Aperture'
    aperture_data.identifier = aperture.identifier
    aperture_data.display_name = aperture.display_name
    data = [aperture_data]
    for shade in aperture.outdoor_shades:
        shade_data = convert_shade(shade)
        data.append(shade_data)
    return data


def convert_face(face: Face) -> List[PolyData]:
    """Convert a HBFace to a PolyData."""
    polydata = convert_face_3d(face.punched_geometry)
    polydata.type = face.type.name
    polydata.identifier = face.identifier
    polydata.display_name = face.display_name
    data = [polydata]
    for aperture in face.apertures:
        data.extend(convert_aperture(aperture))
    return data


def convert_room(room: Room) -> List[PolyData]:
    """Convert HB Room to PolyData."""
    data = []
    for face in room.faces:
        data.extend(convert_face(face))

    return data


def convert_points(points: List[Point3D]) -> PolyData:
    """Export a list of points to VTK.

    Args:
        points : A list of Point3D.

    Returns:
        A vtk object with multiple VTK point objects.
    """
    vtk_points = vtk.vtkPoints()
    vtk_vertices = vtk.vtkCellArray()

    for point in points:
        vtk_points.InsertNextPoint(tuple(point))

    vtk_vertices.InsertNextCell(len(points), list(range(len(points))))

    polydata = PolyData()
    polydata.SetPoints(vtk_points)
    polydata.SetVerts(vtk_vertices)
    polydata.Modified()

    return polydata


def _create_lines(
        start_points: List[Point3D], vectors: List[Vector3D]) -> vtk.vtkPolyData:
    """Create a line from start and end point."""
    # Create a vtkPoints container and store the points for all the lines
    lines_data = vtk.vtkPolyData()
    pts = vtk.vtkPoints()
    for st_pt, vector in zip(start_points, vectors):
        end_pt = st_pt.move(vector)
        pts.InsertNextPoint(st_pt)
        pts.InsertNextPoint(end_pt)

    # add all the points to lines dataset
    lines_data.SetPoints(pts)

    lines = vtk.vtkCellArray()
    # create lines based on points
    for count in range(len(start_points)):
        line = vtk.vtkLine()
        # the second 0 is the index of p0 in linesPolyData's points
        line.GetPointIds().SetId(0, 2 * count)
        # the second 1 is the index of P1 in linesPolyData's points
        line.GetPointIds().SetId(1, (2 * count) + 1)
        lines.InsertNextCell(line)

    lines_data.SetLines(lines)

    return lines_data


def _create_cone(
    center: Point3D, vector: Vector3D, radius: float = 0.1, height: float = 0.3,
    resolution: int = 2
        ) -> PolyData:
    cone_poly = vtk.vtkPolyData()

    # Parameters for the cone
    cone_source = vtk.vtkConeSource()
    cone_source.SetResolution(resolution)
    cone_source.SetRadius(radius)
    cone_source.SetHeight(height)
    cone_source.SetDirection(tuple(vector))
    cone_source.SetCenter(tuple(center))
    cone_source.Update()

    cone_poly.ShallowCopy(cone_source.GetOutput())

    return cone_poly


# TODO: Add an optional input for data
def create_arrow(start_points: List[Point3D], vectors: List[Vector3D]) -> JoinedPolyData:
    """Create arrows from point and vector."""
    assert len(start_points) == len(vectors), \
        'Number of start points must match the number of vectors.'
    cones = []
    lines = _create_lines(start_points, vectors)
    for st_pt, vector in zip(start_points, vectors):
        end_pt = st_pt.move(vector)
        cones.append(_create_cone(end_pt, vector))
    return JoinedPolyData.from_polydata([lines] + cones)


def create_polyline(points: List[Point3D]) -> PolyData:
    """Create a polyline from a list of points."""
    # Create a vtkPoints container and store the points for all the lines
    pts = vtk.vtkPoints()
    for pt in points:
        pts.InsertNextPoint(tuple(pt))

    # add all the points to lines dataset
    polyline = vtk.vtkPolyLine()
    polyline.GetPointIds().SetNumberOfIds(len(points))
    for i in range(len(points)):
        polyline.GetPointIds().SetId(i, i)

    # Create a cell array to store the lines in and add the lines to it
    cells = vtk.vtkCellArray()
    cells.InsertNextCell(polyline)

    # Create a polydata to store everything in
    polydata = PolyData()

    # Add the points to the dataset
    polydata.SetPoints(pts)

    # Add the lines to the dataset
    polydata.SetLines(cells)

    return polydata


def convert_polyline(polyline: Polyline3D) -> PolyData:
    return create_polyline(polyline.vertices)
