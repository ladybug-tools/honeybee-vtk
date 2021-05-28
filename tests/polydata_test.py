"""Unit tests for Polydata class."""

import pytest
import csv
from honeybee_vtk.model import Model


def test_polydata_length():
    file_path = r'./tests/assets/gridbased.hbjson'
    model = Model.from_hbjson(hbjson=file_path)

    with open('shades.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([" "])

        for data in model.shades.data:
            for i in range(data.GetNumberOfPoints()):
                pt = data.GetPoint(i)
                writer.writerow([pt])
            writer.writerow([" "])

    
