# honeybee-vtk
🐝 VTK - Honeybee extension for viewing HBJSON in a web browser.

![HBJSON exported to web](/images/room.gif)

[![Build Status](https://github.com/ladybug-tools/honeybee-vtk/workflows/CI/badge.svg)](https://github.com/ladybug-tools/honeybee-vtk/actions)
[![Coverage Status](https://coveralls.io/repos/github/ladybug-tools/honeybee-vtk/badge.svg)](https://coveralls.io/github/ladybug-tools/honeybee-vtk)
[![Python 3.7](https://img.shields.io/badge/python-3.7-green.svg)](https://www.python.org/downloads/release/python-370/)

[![GitHub tag (latest by date)](https://img.shields.io/github/v/tag/ladybug-tools/honeybee-vtk)](https://github.com/ladybug-tools/honeybee-vtk/releases)
[![GitHub](https://img.shields.io/github/license/ladybug-tools/honeybee-vtk)](https://github.com/ladybug-tools/honeybee-vtk/blob/master/LICENSE)


[![GitHub last commit](https://img.shields.io/github/last-commit/ladybug-tools/honeybee-vtk)](https://github.com/ladybug-tools/honeybee-vtk/commits/master)
[![GitHub issues](https://img.shields.io/github/issues/ladybug-tools/honeybee-vtk)](https://github.com/ladybug-tools/honeybee-vtk/issues)
[![GitHub closed issues](https://img.shields.io/github/issues-closed-raw/ladybug-tools/honeybee-vtk)](https://github.com/ladybug-tools/honeybee-vtk/issues?q=is%3Aissue+is%3Aclosed)

## Installation

```console
pip install honeybee-vtk
```

## QuickStart

```python
import honeybee_vtk
```
## Usage
```console
Usage: honeybee-vtk translate [OPTIONS] HBJSON_FILE

  Translate a HBJSON file to several VTK, XML, or HTML file.

  The output file is either a zipped file that contains all the generated
  VTK/XML files or an HTML file.

  Args:
      hbjson-file: Path to input HBJSON file.

Options:
  -n, --name TEXT                 Name of the output file. If not provided,
                                  the name of input HBJSON file will be used.

  -f, --folder DIRECTORY          Path to target folder.  [default: .]
  -t, --file-type [vtk|xml|html]  Switch between VTK, XML, and HTML formats.
                                  Default is HTML.  [default: html]

  -ig, --include-grids            Export grids.  [default: False]
  -is, --include-sensors [vectors|points]
                                  Export sensors as either arrows or color-
                                  grouped points.

  -in, --include-normals [vectors|points]
                                  Export aperture normals as either arrows or
                                  color-grouped points.

  -sh, --show-html, --show        Open the generated HTML file in a browser.
                                  [default: False]

  --help                          Show this message and exit.
```

Viewing an [HBJSON](tests/assets/gridbased.hbjson) generated from a model that ships with Ladybug Tools. You can send this HTML to someone and they will be able to open the see the same model.

```console
honeybee-vtk translate "path to hbjson file" --include-grids --include-sensors="vectors" --show
```

![](/images/honeybee-vtk-vectors.gif)

Exporting points colored based on the direction of the normals for apertures and grid sensors. This is useful for models with very high number of sensors or apertures.

```console
honeybee-vtk translate "path to hbjson file" --include-grids --include-sensors="points" --include-normals="points" --show
```

![](/images/honeybee-vtk-points.gif)

Saving the files in VTK format and then viewing in [Paraview Glance](https://kitware.github.io/paraview-glance/app/). This is useful if you prefer smaller file sizes. Use "xml" in file-type to export XML files. If you wish to share a model that you have formatted in Paraview Glance, click on "Save State" button in the navbar of Paraview Glance. This will download a .glance file that you can share with others and they will be able to load this file back in Paraview Glance and see the model the way you formatted it.

```console
honeybee-vtk translate "path to hbjson file" --folder="path to the target folder" --file-type="vtk"
```

![](/images/honeybee-vtk-vtk.gif)

## [API Documentation](https://www.ladybug.tools/honeybee-vtk/docs/)


## Create arrows and write to a vtp file

```python
from ladybug_geometry.geometry3d import Point3D, Vector3D
from honeybee_vtk.to_vtk import create_arrow

points = [Point3D(0, 0, 0), Point3D(1, 1, 0), Point3D(1, 0, 0)]
vectors = [Vector3D(0, 0, 1), Vector3D(1, 1, 1), Vector3D(2, 0, 0)]
arrows = create_arrow(points, vectors)
arrows.to_vtk('.', 'arrows')

```

![arrows](/images/arrows.png)

## Create a group of points and color them based on distance from origin

```python

from ladybug_geometry.geometry3d import Point3D
from honeybee_vtk.to_vtk import convert_points

points = []
for x in range(-50, 50, 5):
    for y in range(-50, 50, 5):
        for z in range(-50, 50, 5):
            points.append(Point3D(x, y, z))

origin = Point3D(0, 0, 0)
distance = [pt.distance_to_point(origin) for pt in points]

# convert points to polydata
pts = convert_points(points)
pts.add_data(distance, name='distance', cell=False)
pts.color_by('distance', cell=False)
pts.to_vtk('.', 'colored_points')

```

![arrows](/images/colored_points.png)


## Draw a sunpath

```python
from ladybug.location import Location
from ladybug.sunpath import Sunpath, Point3D, Vector3D
from honeybee_vtk.to_vtk import convert_polyline, create_polyline
from honeybee_vtk.types import JoinedPolyData
import math

# Create location. You can also extract location data from an epw file.
sydney = Location('Sydney', 'AUS', latitude=-33.87, longitude=151.22, time_zone=10)

# Initiate sunpath
sp = Sunpath.from_location(sydney)

radius = 100
origin = Point3D(0, 0, 0)
polylines = sp.hourly_analemma_polyline3d(origin=origin, daytime_only=True, radius=radius)
sp_pls = [convert_polyline(pl) for pl in polylines]

# add a circle
north = origin.move(Vector3D(0, radius, 0))
plot_points = [
    north.rotate_xy(math.radians(angle), origin)
    for angle in range(0, 365, 5)
]

plot = create_polyline(plot_points)

# join polylines into a single polydata
sunpath = JoinedPolyData.from_polydata(sp_pls)
# add plot
sunpath.append(plot)

sunpath.to_vtk('.', 'sunpath')
```

![sunpath](/images/sunpath.png)


## Draw a sunpath with hourly data

```python

from ladybug.epw import EPW
from ladybug.sunpath import Sunpath, Point3D, Vector3D
from honeybee_vtk.to_vtk import convert_points, convert_polyline, create_polyline
from honeybee_vtk.types import JoinedPolyData
import math

# Get location from epw file
epw = EPW('./tests/assets/in.epw')
location = epw.location

# Initiate sunpath
sp = Sunpath.from_location(location)

radius = 100
origin = Point3D(0, 0, 0)
polylines = sp.hourly_analemma_polyline3d(origin=origin, daytime_only=True, radius=radius)
sp_pls = [convert_polyline(pl) for pl in polylines]

# add a circle
north = origin.move(Vector3D(0, radius, 0))
plot_points = [
    north.rotate_xy(math.radians(angle), origin)
    for angle in range(0, 365, 5)
]

plot = create_polyline(plot_points)

# join polylines into a single polydata
sunpath = JoinedPolyData.from_polydata(sp_pls)
# add plot
sunpath.append(plot)
sunpath.to_vtk('.', 'sunpath')

# add sun positions and color them based on radiation
day = sp.hourly_analemma_suns(daytime_only=True)
# calculate sun positions from sun vector
pts = []
hours = []
for suns in day:
    for sun in suns:
        pts.append(origin.move(sun.sun_vector.reverse() * radius))
        hours.append(sun.hoy)

radiation_data = epw.global_horizontal_radiation
filtered_radiation_data = radiation_data.filter_by_hoys(hours)

sun_positions = convert_points(pts)
sun_positions.add_data(
    filtered_radiation_data.values, name='Globale Horizontal Radiation', cell=False
)
sun_positions.color_by('Global Horizontal Radiation', cell=False)
sun_positions.to_vtk('.', 'sun_positions')

```

![sunpath with data](/images/sunpath_with_data.png)


## Load HB model

```python
from honeybee_vtk.model import Model

hbjson = r'./tests/assets/gridbased.hbjson'
model = Model.from_hbjson(hbjson)
model.to_html(folder='.', name='two-rooms', show=True)

```

![HBJSON model](/images/hbjson_model.png)


## Load HB model - change display model and colors

```python

from honeybee_vtk.model import Model, DisplayMode
from ladybug.color import Color

hbjson = r'./tests/assets/gridbased.hbjson'
model = Model.from_hbjson(hbjson)

# update model visualization to show edges
model.update_display_mode(DisplayMode.SurfaceWithEdges)

# set shades to wireframe mode and change their color to black
model.shades.display_mode = DisplayMode.Wireframe
model.shades.color = Color(0, 0, 0, 255)

model.to_html('.', name='two-rooms', show=True)
```

![Modified HBJSON model](/images/hbjson_model_2.png)
