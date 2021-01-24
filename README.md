# honeybee-vtk
🐝 VTK - Honeybee extension for viewing HBJSON in a web browser.

![HBJSON exported to web](/images/room.gif)

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
honeybee-vtk translate --help

Usage: honeybee-vtk translate [OPTIONS] HBJSON_FILE

  Translate a HBJSON file to several VTK, XML, or HTML file.

  The output file is either a zipped file that contains all the generated
  VTK/XML files  or an HTML file.

Args:
    hbjson-file: Path to input HBJSON file.

Options:
  -n, --name TEXT                 Name of the output file. If not provided, the name of input HBJSON file will be used.

  -f, --folder DIRECTORY          Path to target folder.  [default: .]
  
  -t, --file-type [vtk|xml|html]  Switch between VTK, XML, and HTML formats. Default is HTML.  [default: html]

  -eg, --include-grids            Export grids.  [default: False]
  
  -ev, --include-vectors          Export normals for apertures and grid sensors.  [default: False]

  -ep, --include-points           Export points colored based on the direction of normal for apertures and grid sensors.  [default: False]

  -sh, --show-html, --show        Open the generated HTML file in a browser. [default: False]

  --help                          Show this message and exit.
```

Viewing an [HBJSON](tests/assets/gridbased.hbjson) generated from a model that ships with Ladybug Tools. You can send this HTML to someone and they will be able to open the see the same model.

```console
honeybee-vtk translate "path to hbjson file" --include-grids --include-vectors --show
```

![](/images/honeybee-vtk-vectors.gif)

Exporting points colored based on the direction of the normals for apertures and grid sensors. This is useful for models with very high number of sensors or apertures.

```console
honeybee-vtk translate "path to hbjson file" --include-grids --include-points --show
```

![](/images/honeybee-vtk-points.gif)

Saving the files in VTK format and then viewing in [Paraview Glance](https://kitware.github.io/paraview-glance/app/). This is useful if you prefer smaller file sizes. Use "xml" in file-type to export XML files. If you wish to share a model that you have formatted in Paraview Glance, click on "Save State" button in the navbar of Paraview Glance. This will download a .glance file that you can share with others and they will be able to load this file back in Paraview Glance and see the model the way you formatted it.

```console
honeybee-vtk translate "path to hbjson file" --folder="path to the target folder" --file-type="vtk"
```

![](/images/honeybee-vtk-vtk.gif)

## [API Documentation](https://www.ladybug.tools/honeybee-vtk/docs/)
