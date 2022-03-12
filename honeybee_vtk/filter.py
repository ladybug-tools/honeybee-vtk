"""Filters to be used with VTK."""

import vtk


def filter_using_thresholds(polydata: vtk.vtkPolyData, lower_threshold: float = None,
                            upper_threshold: float = None) -> vtk.vtkPolyData:
    """Apply a threshold filter to a polydata.

    This function will remove the cell or points of the Polydata that fall outside of
    the given thresholds. This function first applies the vtkThreshold filter to the
    polydata and then uses the vtkDataSetSurfaceFilter to turn the
    vtkUnstructuredGrid into a vtkPolyData.

    Args:
        polydata: A vtkPolyData object.
        lower_threshold: The lower threshold value. This threshold value is included
            in the thresholding operation. For example, if you want the threshold to be
            greater than 0 then set the value 0.1. If None, lower threshold will 
            be inifinite.
        upper_threshold: The upper threshold value. This threshold value is included in
            the thresholding operation. For example, if you wan to the threshold to be
            lower than 1 then set the value 0.99. If None, upper threshold will
            be inifinite.

    Returns:
        A vtkPolyData object.
    """
    if lower_threshold is None and upper_threshold is None:
        return polydata

    threshold = vtk.vtkThreshold()
    threshold.SetInputData(polydata)
    if lower_threshold is not None:
        threshold.SetLowerThreshold(lower_threshold)
    if upper_threshold is not None:
        threshold.SetUpperThreshold(upper_threshold)
    threshold.AllScalarsOn()
    threshold.Update()

    surfacefilter = vtk.vtkDataSetSurfaceFilter()
    surfacefilter.SetInputData(threshold.GetOutput())
    surfacefilter.Update()

    return surfacefilter.GetOutput()
