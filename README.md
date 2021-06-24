# honeybee-vtk
🐝 VTK - Honeybee extension for viewing HBJSON in a web browser.

![HBJSON exported to web](/images/room.gif)

[![Build Status](https://github.com/ladybug-tools/honeybee-vtk/workflows/CI/badge.svg)](https://github.com/ladybug-tools/honeybee-vtk/actions)
[![Coverage Status](https://coveralls.io/repos/github/ladybug-tools/honeybee-vtk/badge.svg?branch=master)](https://coveralls.io/github/ladybug-tools/honeybee-vtk?branch=master)
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
## Translate a HBJSON file to an HTML or vtkjs file
```console
Usage: honeybee-vtk translate [OPTIONS] HBJSON_FILE

  Translate a HBJSON file to an HTML or a vtkjs file.

  Args:
      hbjson-file: Path to an HBJSON file.

Options:
  -n, --name TEXT                 Name of the output file.  [default: model]
  -f, --folder DIRECTORY          Path to target folder.  [default: .]
  -ft, --file-type [html|vtkjs]   Switch between html and vtkjs formats
                                  [default: html]

  -dm, --display-mode [shaded|surface|surfacewithedges|wireframe|points]
                                  Set display mode for the model.  [default:
                                  shaded]

  -go, --grid-options [ignore|points|meshes]
                                  Export sensor grids as either points or
                                  meshes.  [default: ignore]

  -sh, --show-html, --show        Open the generated HTML file in a browser.
                                  [default: False]

  --help                          Show this message and exit.
```

## Export images from an HBJSON file
```console
Usage: honeybee-vtk export-images [OPTIONS] HBJSON_FILE

  Export images from radiance views in a HBJSON file.

  Args:
      hbjson-file: Path to an HBJSON file.

Options:
  -n, --name TEXT                 Name of image files.  [default: Camera]
  -f, --folder DIRECTORY          Path to target folder.  [default: .]
  -it, --image-type [png|jpg|ps|tiff|bmp|pnm]
                                  choose the type of image file.  [default:
                                  jpg]

  -iw, --image-width INTEGER      Width of images in pixels.  [default: 2500]
  -ih, --image-height INTEGER     Height of images in pixels.  [default: 2000]
  -bc, --background-color <INTEGER INTEGER INTEGER>...
                                  Set background color for images  [default:
                                  255, 255, 255]

  -dmm, --display-mode-model [shaded|surface|surfacewithedges|wireframe|points]
                                  Set display mode for the model.  [default:
                                  shaded]

  -go, --grid-options [ignore|points|meshes]
                                  Export sensor grids as either points or
                                  meshes.  [default: ignore]

  -dmg, --display-mode-grid [shaded|surface|surfacewithedges|wireframe|points]
                                  Set display mode for the Sensorgrids.
                                  [default: shaded]

  -vf, --view PATH                File Path to the Radiance view file.
                                  Multiple view files are accepted.

  -cf, --config PATH              File Path to the config json file which can
                                  be used to mount simulation data on HBJSON.

  --help                          Show this message and exit.
```
## Create arrows and write to a vtp file and open it in a minimalist desktop [viewer](https://kitware.github.io/F3D/)

```python
from ladybug_geometry.geometry3d import Point3D, Vector3D
from honeybee_vtk.to_vtk import create_arrow

points = [Point3D(0, 0, 0), Point3D(1, 1, 0), Point3D(1, 0, 0)]
vectors = [Vector3D(0, 0, 1), Vector3D(1, 1, 1), Vector3D(2, 0, 0)]
arrows = create_arrow(points, vectors)
arrows.to_vtk('.', 'arrows')

```
![arrows](/images/arrows.png)

## Create a group of points and color them based on distance from origin, write them to a vtp file and and open it in a minimalist desktop [viewer](https://kitware.github.io/F3D/)

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


## Load HB model - change display mode and colors

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

# create an HTML file with embedded visualization. You can share this HTML as is
# and it will include all the information.
model.to_html('.', name='two-rooms', show=True)

# alternatively you can write it as a vtkjs file and visualize it in ParaviewGlance
# the `to_html` method calls this method under the hood.
# model.to_vtkjs(folder='.')

```

![Modified HBJSON model](/images/hbjson_model_2.png)


## Load HB Model and daylight factor results

```python

from honeybee_vtk.model import Model, DisplayMode, SensorGridOptions
import pathlib

hbjson = r'./tests/assets/revit_model/model.hbjson'
results_folder = r'./tests/assets/revit_model/df_results'

model = Model.from_hbjson(hbjson, load_grids=SensorGridOptions.Mesh)

# load the results for each grid
# note that we load the results using the order for model to ensure the order will match
daylight_factor = []
for grid in model.sensor_grids.data:
    res_file = pathlib.Path(results_folder, f'{grid.identifier}.res')
    grid_res = [float(v) for v in res_file.read_text().splitlines()]
    daylight_factor.append(grid_res)

# add the results to sensor grids as a new field
# per face is set to True since we loaded grids as a mesh
model.sensor_grids.add_data_fields(daylight_factor, name='Daylight Factor', per_face=True)
model.sensor_grids.color_by = 'Daylight Factor'

# make it pop!
# change display mode for sensor grids to be surface with edges
model.sensor_grids.display_mode = DisplayMode.SurfaceWithEdges
# update model visualization to wireframe
model.update_display_mode(DisplayMode.Wireframe)
# make shades to be shaded with edge
model.shades.display_mode = DisplayMode.SurfaceWithEdges

# export the model to a HTML file with embedded viewer and open the page in a browser
model.to_html('c:/ladybug', name='revit-model', show=True)

# alternatively you can write it as a vtkjs file and visualize it in ParaviewGlance
# the `to_html` method calls this method under the hood.
# model.to_vtkjs(folder='.')

```

![Daylight factor results](/images/revit_model_daylight_factor.png)


## Load HB Model and annual daylight results

```python

from honeybee_vtk.model import Model, DisplayMode, SensorGridOptions
import pathlib

hbjson = r'./tests/assets/gridbased.hbjson'
results_folder = r'./tests/assets/annual_metrics'

model = Model.from_hbjson(hbjson, load_grids=SensorGridOptions.Mesh)

# load the results for each grid
# note that we load the results using the order for model to ensure the order will match
annual_metrics = [
    {'folder': 'da', 'extension': 'da', 'name': 'Daylight Autonomy'},
    {'folder': 'cda', 'extension': 'cda', 'name': 'Continuous Daylight Autonomy'},
    {'folder': 'udi', 'extension': 'udi', 'name': 'Useful Daylight Illuminance'},
    {'folder': 'udi_lower', 'extension': 'udi', 'name': 'Lower Daylight Illuminance'},
    {'folder': 'udi_upper', 'extension': 'udi', 'name': 'Excessive Daylight Illuminance'}
]
for metric in annual_metrics:
    results = []
    for grid in model.sensor_grids.data:
        res_file = pathlib.Path(
            results_folder, metric['folder'], f'{grid.identifier}.{metric["extension"]}'
        )
        grid_res = [float(v) for v in res_file.read_text().splitlines()]
        results.append(grid_res)

    # add the results to sensor grids as a new field
    # per face is set to True since we loaded grids as a mesh
    model.sensor_grids.add_data_fields(results, name=metric['name'], per_face=True)

# Set color by to Useful Daylight Illuminance
model.sensor_grids.color_by = 'Useful Daylight Illuminance'

# make it pop!
# change display mode for sensor grids to be surface with edges
model.sensor_grids.display_mode = DisplayMode.SurfaceWithEdges
# update model visualization to wireframe
model.update_display_mode(DisplayMode.Wireframe)

# export the model to a HTML file with embedded viewer and open the page in a browser
model.to_html('.', name='two-rooms', show=True)

# alternatively you can write it as a vtkjs file and visualize it in ParaviewGlance
# the `to_html` method calls this method under the hood.
# model.to_vtkjs(folder='.')

```

![Annual daylight results](/images/annual_daylight_metrics.png)


## Save model with results as an image



```python
from honeybee_vtk.model import Model, DisplayMode, SensorGridOptions
from honeybee_vtk.scene import Scene

import pathlib

hbjson = r'./tests/assets/gridbased.hbjson'
results_folder = r'./tests/assets/df_results'

model = Model.from_hbjson(hbjson, load_grids=SensorGridOptions.Mesh)

# load the results for each grid
# note that we load the results using the order for model to ensure the order will match
daylight_factor = []
for grid in model.sensor_grids.data:
    res_file = pathlib.Path(results_folder, f'{grid.identifier}.res')
    grid_res = [float(v) for v in res_file.read_text().splitlines()]
    daylight_factor.append(grid_res)

# add the results to sensor grids as a new field
# per face is set to True since we loaded grids as a mesh
model.sensor_grids.add_data_fields(
    daylight_factor, name='Daylight Factor', per_face=True, data_range=(0, 20)
)
model.sensor_grids.color_by = 'Daylight Factor'

# make it pop!
# change display mode for sensor grids to be surface with edges
model.sensor_grids.display_mode = DisplayMode.SurfaceWithEdges
# update model visualization to wireframe
model.update_display_mode(DisplayMode.Wireframe)
# make shades to be shaded with edge
model.shades.display_mode = DisplayMode.SurfaceWithEdges

# create a scene to render the model
scene = Scene()
scene.add_model(model)
# set a scale bar based on daylight factor values
color_range = model.sensor_grids.active_field_info.color_range()

# you can also save the scene as an image.
# right now you can't control the camera but camera control can be implemented.
scene.to_image('.', name='daylight_factor', image_scale=2, color_range=color_range)

# alternatively you can start an interactive window
# scene.show(color_range)

```

![Captured image](/images/captured_daylight_factor.png)

![Interactive renderer](/images/interactive_scene.png)
