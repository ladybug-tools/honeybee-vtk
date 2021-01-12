"""Functions to create vtk objects based on the data extracted from hbjson."""

import vtk


def group_by_face_type(points_lst, hb_types):
    """Group points based on Honeybee type.

    Args:
        points_lst: A list of lists of points for the geometry in the HBJSON. Here,
            each point is a list of X, Y, and Z cordinates of the point.
        hb_types: A list of honeybee face_types and/or types for the geometry objects
            in the HBJSON.

    Returns:
        A dictionary with Honeybee type as keys and list of list of points for geometry
        that belongs to that Honeybee type.
    """
    grouped_points = {face_type: [] for face_type in hb_types}

    for i in range(len(hb_types)):
        grouped_points[hb_types[i]].append(points_lst[i])

    return grouped_points


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


def create_polygons(points_lst):
    """Create a vtk object with multiple vtk polygons.

    Args:
        points_lst: A list of lists of points. Here, each point is a list of X, Y, 
            and Z cordinate.

    Returns:
        A vtk object that with multiple polygons.
    """
    vtk_polydata_lst = []

    for i in range(len(points_lst)):

        vtk_points, vtk_polygon = create_polygon(points_lst[i])
        vtk_polygons = vtk.vtkCellArray()
        vtk_polygons.InsertNextCell(vtk_polygon)

        vtk_polydata = vtk.vtkPolyData()
        vtk_polydata.SetPoints(vtk_points)
        vtk_polydata.SetPolys(vtk_polygons)
        vtk_polydata.Modified()

        vtk_polydata_lst.append(vtk_polydata)

    vtk_polydata_extended = vtk.vtkAppendPolyData()
    
    for i in range(len(vtk_polydata_lst)):
        vtk_polydata_extended.AddInputData(vtk_polydata_lst[i])

    vtk_polydata_extended.Update()

    return vtk_polydata_extended


def write_polydata(polydata, file_name):
    """Write a VTK file to the disk.

    Args:
        polydata: An appended VTK polydata object.
        file_name: A text string for the the file name to be written.
    """
    vtk_polydata_extended = create_polygons(polydata)
    writer = vtk.vtkPolyDataWriter()
    writer.SetFileName(file_name + '.vtk')
    writer.SetInputConnection(vtk_polydata_extended.GetOutputPort())
    writer.Write()


def write_color_grouped_points(points, vectors, file_name='grid points'):
    """Write color-grouped VTK points to disk.

    Args:
        points : A list of points. Here, each points is a list of X, Y, and Z
            cordinates of the point.
        vectors: A list of grid vectors where each vector is a list of X, Y, and Z
            component of a vector.
        file_name: A text string to be used as a file name. Defaults to "grid points."
    """
    point_polydata = point_vectors(points, vectors)
    writer = vtk.vtkPolyDataWriter()
    writer.SetFileName(file_name + '.vtk')
    writer.SetInputData(point_polydata)
    writer.Write()


def write_arrows(start_points, end_points, normals, file_name):
    """Write VTK arrows to the disk.

    Args:
        start_points: A list Ladybug Point3D objects. These are start points for
            each Face3D created from points provided to the function.
        end_points: A list of Ladybug Point3D objects. These points are derived by
            moving the center point of a Face3D using the vector of the Face3D.
        normals: A list of Ladybug Vector3D objects.
        file_name: A text string to be used as the file name.
    """
    face_vector_polydata = create_arrows(start_points, end_points, normals)
    writer = vtk.vtkPolyDataWriter()
    writer.SetFileName(file_name + ' vectors.vtk')
    writer.SetInputConnection(face_vector_polydata.GetOutputPort())
    writer.Write()


def create_arrows(start_points, end_points, vectors):
    """Create an Arrow in VTK using a start point, end point and a vector.

    Args:
        start_points: A list of list of points. Here, each point is a list of X, Y, 
            and Z cordinate.
        end_points: A list of list of points. Here, each point is a list of X, Y, 
            and Z cordinate.
        vectors: A list of vectors for the grid points. Here, each vector is a list 
            of X, Y, and Z components of a vector.

    Returns:
        A vtk object with multiple VTK objects that would look like arrows.
    """
   
    lines_polydata = []
    cones_polydata = []

    for i in range(len(start_points)):
        linesPolyData = vtk.vtkPolyData()
        # Create three points
        p0 = start_points[i]
        p1 = end_points[i]

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
        coneSource.SetDirection(tuple(vectors[i]))
        coneSource.SetCenter(tuple(p1))
        coneSource.Update()

        conePoly.ShallowCopy(coneSource.GetOutput())
        cones_polydata.append(conePoly)
        
    vtk_polydata_extended = vtk.vtkAppendPolyData()

    for i in range(len(lines_polydata)):
        vtk_polydata_extended.AddInputData(lines_polydata[i])

    for i in range(len(cones_polydata)):
        vtk_polydata_extended.AddInputData(cones_polydata[i])

    vtk_polydata_extended.Update()

    return vtk_polydata_extended


def point_vectors(start_points, vectors):
    """Export points to VTK and color-group them based on vectors.

    Args:
        start_points: A list of list of points. Here, each point is a list of X, Y, 
            and Z cordinate.
        vectors: A list of vectors for the grid points. Here, each vector is a list 
            of X, Y, and Z components of a vector.

    Returns:
        A vtk object with multiple VTK objects that would look like color-grouped points.
    """
    points_polydata = []

    points = vtk.vtkPoints()
    vertices = vtk.vtkCellArray()

    for i in range(len(start_points)):
        pid = [0]
        pid[0] = points.InsertNextPoint(start_points[i])
        vertices.InsertNextCell(1, pid)

    normals = vtk.vtkFloatArray()
    normals.SetNumberOfComponents(3)
    normals.SetNumberOfTuples(len(vectors))
    for i in range(len(vectors)):
        normals.InsertNextTuple3(vectors[i][0], vectors[i][1], vectors[i][2])
    
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
    values.SetNumberOfComponents(1)
    for vector in vectors:
        value = vector_dict[
            str(round(vector[0])) + str(round(vector[1])) + str(round(vector[2]))]
        values.InsertNextValue(value)

    polydata = vtk.vtkPolyData()
    polydata.SetPoints(points)
    polydata.SetVerts(vertices)
    polydata.GetCellData().SetScalars(values)
    polydata.Modified()

    return polydata


def create_cones(start_points, vectors):
    """Create VTK cones at point locations.

    Args:
        start_points: A list of list of points. Here, each point is a list of X, Y, 
            and Z cordinate.
        vectors: A list of vectors for the grid points. Here, each vector is a list 
            of X, Y, and Z components of a vector.

    Returns:
        A vtk object with multiple VTK objects that would look like arrow heads (cones).
    """

    cones_polydata = []

    for i in range(len(start_points)):
        conePoly = vtk.vtkPolyData()

        # Parameters for the cone
        coneSource = vtk.vtkConeSource()
        coneSource.SetResolution(1)
        coneSource.SetRadius(0.1)
        coneSource.SetHeight(0.3)
        coneSource.SetDirection(tuple(vectors[i]))
        coneSource.SetCenter(tuple(start_points[i]))
        coneSource.Update()

        conePoly.ShallowCopy(coneSource.GetOutput())
        cones_polydata.append(conePoly)

    vtk_polydata_extended = vtk.vtkAppendPolyData()

    for i in range(len(cones_polydata)):
        vtk_polydata_extended.AddInputData(cones_polydata[i])

    vtk_polydata_extended.Update()

    return vtk_polydata_extended

