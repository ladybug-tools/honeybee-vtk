# honeybee-vtk
🐝 VTK - Honeybee extension for viewing HBJSON in a web browser.

![HBJSON exported to web](/images/room.gif)

[![Build Status](https://github.com/ladybug-tools/honeybee-vtk/workflows/CI/badge.svg)](https://github.com/ladybug-tools/honeybee-vtk/actions)
[![Coverage Status](https://coveralls.io/repos/github/ladybug-tools/honeybee-vtk/badge.svg)](https://coveralls.io/github/ladybug-tools/honeybee-vtk)
[![Python 3.7](https://img.shields.io/badge/python-3.7-green.svg)](https://www.python.org/downloads/release/python-370/)

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
