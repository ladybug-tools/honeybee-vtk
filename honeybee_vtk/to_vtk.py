"""Functions to create vtk objects based on the data extracted from hbjson."""

import vtk
from typing import List


def create_polygon(points):
    """Create a vtk Polygon from a list of points.

    The point will have to be in an order. This function cannot be used to create a
    polygon with holes.

    Args:
        points: A list of points. Here, each point is a list of X, Y, and Z cordinate.

    Returns:
        A tuple with two elements.

        - vtk_points: A list of vtk point objects

        - vtk_polygon: A vtk polygon object created from the points provided.
    """
    vtk_points = vtk.vtkPoints()
    vtk_polygon = vtk.vtkPolygon()
    vtk_polygon.GetPointIds().SetNumberOfIds(len(points))

    for point in points:
        vtk_points.InsertNextPoint(tuple(point))

    for i in range(len(points)):
        vtk_polygon.GetPointIds().SetId(i, i)

    return vtk_points, vtk_polygon


def create_polygons(points: List[List]) -> vtk.vtkAppendPolyData:
    """Create a vtk object with multiple vtk polygons.

    Args:
        points: A list of lists of Ladybug Point3D objects.

    Returns:
        A vtk object with multiple polygons.
    """
    vtk_polydata_to_append = []

    for point in points:

        vtk_points, vtk_polygon = create_polygon(point)
        vtk_polygons = vtk.vtkCellArray()
        vtk_polygons.InsertNextCell(vtk_polygon)

        vtk_polydata = vtk.vtkPolyData()
        vtk_polydata.SetPoints(vtk_points)
        vtk_polydata.SetPolys(vtk_polygons)
        vtk_polydata.Modified()

        vtk_polydata_to_append.append(vtk_polydata)

    vtk_polydata_extended = vtk.vtkAppendPolyData()

    for vtk_polydata in vtk_polydata_to_append:
        vtk_polydata_extended.AddInputData(vtk_polydata)

    vtk_polydata_extended.Update()

    return vtk_polydata_extended


def create_arrows(start_points, end_points, vectors):
    """Create an Arrow in VTK using a start point, end point and a vector.

    Args:
        start_points: A list of Ladybug Point3D objects.
        end_points: A list of Ladybug Point3D objects.
        vectors: A list of Ladybug Vector3D objects.

    Returns:
        A vtk object with multiple VTK objects that would look like arrows.
    """
    lines_polydata = []
    cones_polydata = []

    for start_point, end_point, vector in zip(start_points, end_points, vectors):
        linesPolyData = vtk.vtkPolyData()
        # Create three points
        p0 = start_point
        p1 = end_point

        # Create a vtkPoints container and store the points in it
        pts = vtk.vtkPoints()
        pts.InsertNextPoint(p0)
        pts.InsertNextPoint(p1)

        # Add the points to the polydata container
        linesPolyData.SetPoints(pts)

        # Create the first line (between Origin and P0)
        line0 = vtk.vtkLine()
        # the second 0 is the index of p0 in linesPolyData's points
        line0.GetPointIds().SetId(0, 0)
        # the second 1 is the index of P1 in linesPolyData's points
        line0.GetPointIds().SetId(1, 1)

        # Create a vtkCellArray container and store the lines in it
        lines = vtk.vtkCellArray()
        lines.InsertNextCell(line0)

        # Add the lines to the polydata container
        linesPolyData.SetLines(lines)
        lines_polydata.append(linesPolyData)

        # Add cone to the end of line
        conePoly = vtk.vtkPolyData()

        # Parameters for the cone
        coneSource = vtk.vtkConeSource()
        coneSource.SetResolution(2)
        coneSource.SetRadius(0.1)
        coneSource.SetHeight(0.3)
        coneSource.SetDirection(tuple(vector))
        coneSource.SetCenter(tuple(p1))
        coneSource.Update()

        conePoly.ShallowCopy(coneSource.GetOutput())
        cones_polydata.append(conePoly)

    vtk_polydata_extended = vtk.vtkAppendPolyData()

    for line in lines_polydata:
        vtk_polydata_extended.AddInputData(line)

    for cone in cones_polydata:
        vtk_polydata_extended.AddInputData(cone)

    vtk_polydata_extended.Update()

    return vtk_polydata_extended


def create_points(points):
    """Export points to VTK.

    Args:
        points : A list of lists. Here, each list has X, Y, and Z coordinates of a point.

    Returns:
        A vtk object with multiple VTK point objects.
    """
    vtk_points = vtk.vtkPoints()
    vtk_vertices = vtk.vtkCellArray()

    for point in points:
        pid = [0]
        pid[0] = vtk_points.InsertNextPoint(point)
        vtk_vertices.InsertNextCell(1, pid)

    polydata = vtk.vtkPolyData()
    polydata.SetPoints(vtk_points)
    polydata.SetVerts(vtk_vertices)
    polydata.Modified()

    return polydata


def create_color_grouped_points(
        points: List[List], vectors: List[List]) -> vtk.vtkPolyData():
    """Export points to VTK and color-group them based on vectors.

    Args:
        points : A list of lists. Here, each list has X, Y, and Z coordinates of a point.
        vectors: A list of lists. Here, each list has X, Y, and Z components of a vector.

    Returns:
        A vtk object with multiple VTK objects that would look like color-grouped points.
    """
    vtk_points = vtk.vtkPoints()
    vtk_vertices = vtk.vtkCellArray()

    for point in points:
        pid= [vtk_points.InsertNextPoint(point)]
        vtk_vertices.InsertNextCell(1, pid)

    normals = vtk.vtkFloatArray()
    normals.SetNumberOfComponents(3)
    normals.SetNumberOfTuples(len(vectors))

    for vector in vectors:
        normals.InsertNextTuple3(*vector)

    # Using the text string of the sum of vector components to perform grouping
    vec_sum = [
        str(round(vector[0])) + str(round(vector[1])) + str(round(vector[2]))
        for vector in vectors]

    unique_vectors = list(set(vec_sum))

    # A dictionary with unique vector : unique integer structure.
    # These unique integers wil be used in scalars to color the points grouped based
    # on the unique vectors
    vector_dict = {}
    for count, item in enumerate(unique_vectors):
        vector_dict[item] = count

    values = vtk.vtkIntArray()
    values.SetName('Vectors')
    values.SetNumberOfComponents(1)
    for vector in vectors:
        value = vector_dict[
            str(round(vector[0])) + str(round(vector[1])) + str(round(vector[2]))]
        values.InsertNextValue(value)

    polydata = vtk.vtkPolyData()
    polydata.SetPoints(vtk_points)
    polydata.SetVerts(vtk_vertices)
    polydata.GetCellData().SetScalars(values)
    polydata.GetCellData().SetActiveScalars('Vectors')
    polydata.Modified()

    return polydata


def create_cones(points, vectors):
    """Create VTK cones at point locations.

    Args:
        points : A list of lists. Here, each list has X, Y, and Z coordinates of a point.
        vectors: A list of lists. Here, each list has X, Y, and Z components of a vector.

    Returns:
        A vtk object with multiple VTK objects that would look like arrow heads (cones).
    """

    cones_polydata = []

    for point, vector in zip(points, vectors):
        conePoly = vtk.vtkPolyData()

        # Parameters for the cone
        coneSource = vtk.vtkConeSource()
        coneSource.SetResolution(1)
        coneSource.SetRadius(0.1)
        coneSource.SetHeight(0.3)
        coneSource.SetDirection(tuple(vector))
        coneSource.SetCenter(tuple(point))
        coneSource.Update()

        conePoly.ShallowCopy(coneSource.GetOutput())
        cones_polydata.append(conePoly)

    vtk_polydata_extended = vtk.vtkAppendPolyData()

    for cone in cones_polydata:
        vtk_polydata_extended.AddInputData(cone)

    vtk_polydata_extended.Update()

    return vtk_polydata_extended
