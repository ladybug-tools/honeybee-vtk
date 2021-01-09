"""Functions to create vtk objects based on the data extracted from hbjson."""

import vtk


def group_by_face_type(points_lst, display_names, hb_types):
    """Group points based on Honeybee type.

    Args:
        points_lst: A list of lists of points for the geometry in the HBJSON
        display_names: A list of display names for all the faces in the model
        hb_types: A list of honeybee face_types and/or types for the geometry objects
            in the HBJSON.
        

    Returns:
        A dictionary with Honeybee type as keys and list of list points for geometry
        that belongs to that Honeybee type.
    """
    grouped_points = {face_type: [] for face_type in hb_types}
    grouped_display_names = {face_type: [] for face_type in hb_types}

    for i in range(len(hb_types)):
        grouped_points[hb_types[i]].append(points_lst[i])
        grouped_display_names[hb_types[i]].append(display_names[i])

    return grouped_points, grouped_display_names


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


def create_polygons(points_lst, display_names):
    """Create a vtk object with multiple vtk polygons.

    Args:
        points_lst: A list of lists of points. Here, each point is a list of X, Y, 
            and Z cordinate.

    Returns:
        A vtk object that has multiple vtk polygons.
    """
    vtk_polydata_lst = []

    for i in range(len(points_lst)):
        # Create a list of vtk polydata objects with polygons
        vtk_points, vtk_polygon = create_polygon(points_lst[i])

        vtk_polygons = vtk.vtkCellArray()
        vtk_polygons.InsertNextCell(vtk_polygon)

        # Assgning a text based field data
        vtk_names = vtk.vtkFieldData()
        vtk_display_names = vtk.vtkStringArray()
        vtk_display_names.SetName("Display_names")
        vtk_display_names.InsertNextValue(display_names[i])
        vtk_names.AddArray(vtk_display_names)

        vtk_polydata = vtk.vtkPolyData()
        vtk_polydata.SetPoints(vtk_points)
        vtk_polydata.SetPolys(vtk_polygons)
        vtk_polydata.SetFieldData(vtk_names)
        vtk_polydata.Modified()

        vtk_polydata_lst.append(vtk_polydata)

    # Create a vtk object with multiple polygons
    vtk_polydata_extended = vtk.vtkAppendPolyData()
    for i in range(len(vtk_polydata_lst)):
        vtk_polydata_extended.AddInputData(vtk_polydata_lst[i])
    vtk_polydata_extended.Update()

    return vtk_polydata_extended


def create_arrows(start_points, end_points, vectors):
    """Create lines from start point and end point.

    Args:
        start_points: A list of list of points. Here, each point is a list of X, Y, 
            and Z cordinate.
        end_points: A list of list of points. Here, each point is a list of X, Y, 
            and Z cordinate.
        vectors: A list of vectors for the grid points. Here, each vector is a list 
            of X, Y, and Z values of a vector.

    Returns:
        A vtk object that has multiple vtk lines & cones.
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
    points_polydata = []


    points = vtk.vtkPoints()
    # points.SetNumberOfPoints(len(start_points))
    # for i in range(len(start_points)):
    #     points.InsertNextPoint(tuple(start_points[i]))
    
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


    # vec_sum = [str(round(vector[0],2)) + str(round(vector[1],2)) + str(round(vector[2],2)) for vector in vectors]
    vec_sum = [str(round(vector[0])) + str(round(vector[1])) + str(round(vector[2])) for vector in vectors]
    unique_vectors = list(set(vec_sum))

    vector_dict = {}
    for count, item in enumerate(unique_vectors):
        vector_dict[item] = count

    values = vtk.vtkIntArray()
    values.SetNumberOfComponents(1)
    for vector in vectors:
        # value = vector_dict[str(round(vector[0], 2)) + str(round(vector[1], 2)) + str(round(vector[2], 2))]
        value = vector_dict[str(round(vector[0])) + str(round(vector[1])) + str(round(vector[2]))]
        values.InsertNextValue(value)
    
    polydata = vtk.vtkPolyData()
    polydata.SetPoints(points)
    polydata.SetVerts(vertices)
    # polydata.GetPointData().SetNormals(normals)
    polydata.GetCellData().SetScalars(values)
    polydata.Modified()

    return polydata


def create_cones(start_points, vectors):

    cones_polydata = []

    for i in range(len(start_points)):
        # Add cone to the end of line
        conePoly = vtk.vtkPolyData()

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


def create_mesh(mesh_points):
    
    points_lst = mesh_points
    vtk_polydata_lst = []

    for i in range(len(points_lst)):
            # Create a list of vtk polydata objects with polygons
        vtk_points, vtk_polygon = create_polygon(points_lst[i])

        vtk_polygons = vtk.vtkCellArray()
        vtk_polygons.InsertNextCell(vtk_polygon)

        vtk_polydata = vtk.vtkPolyData()
        vtk_polydata.SetPoints(vtk_points)
        vtk_polydata.SetPolys(vtk_polygons)

        vtk_polydata_lst.append(vtk_polydata)

    # Create a vtk object with multiple polygons
    vtk_polydata_extended = vtk.vtkAppendPolyData()
    
    for i in range(len(vtk_polydata_lst)):
        vtk_polydata_extended.AddInputData(vtk_polydata_lst[i])
    vtk_polydata_extended.Update()

    return vtk_polydata_extended
