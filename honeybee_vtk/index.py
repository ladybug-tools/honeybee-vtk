"""Write index.json to color vtk datasets."""

import os
import json
import copy

# Scarlet colors in decimal
layer_colors = {
    'Wall': [0.858, 0.713, 0.560],
    'Aperture': [0.858, 0.988, 1],
    'Door': [0.776, 0.847, 0.686],
    'Shade': [0.937, 0.643, 0.545],
    'Floor': [0.031, 0.572, 0.647],
    'RoofCeiling': [0.407, 0.325, 0.411],
    'Grid base': [0.925, 0.250, 0.403],
    'Grid mesh': [0.925, 0.250, 0.403],
    'Grid points': [1, 1, 1],
    'Aperture vectors': [1, 1, 1],
    'Grid base vectors': [1, 1, 1],
    'Grid mesh vectors': [1, 1, 1],
    'Grid points vectors': [1, 1, 1],
    'Aperture points': [1, 1, 1],
    'Grid base points': [1, 1, 1],
    'Grid mesh points': [1, 1, 1],
    'AirBoundary': [0.109, 0.227, 0.074],
    'Context': [0.925, 0.305, 0.125]
}

index_template = {
    "version": 1,
    "background": [1, 1, 1],
    "camera": {
        "focalPoint": [2.5, 5, 1.5],
        "position": [19.3843, -6.75305, 10.2683],
        "viewUp": [-0.303079, 0.250543, 0.919441]
    },
    "centerOfRotation": [2.5, 5, 1.5],
    "scene": [],
    "lookupTables": {}
}

dataset_template = {
            "name": None,
            "type": "httpDataSetReader",
            "httpDataSetReader": {"url": None},
            "actor": {
                "origin": [0, 0, 0],
                "scale": [1, 1, 1],
                "position": [0, 0, 0]
            },
            "actorRotation": [0, 0, 0, 1],
            "mapper": {
                "colorByArrayName": "",
                "colorMode": 0,
                "scalarMode": 4
            },
            "property": {
                "representation": 2,
                "edgeVisibility": 0,
                "diffuseColor": None,
                "pointSize": 5,
                "opacity": None
            }
    }


def write_index_json(target_folder, layer_names):
    """write index.json for all the vtk layers.

    This function creates an index.json file that hosts visualization settings to be 
    used in Paraview Glance for each layer.

    Args:
        target_folder: A text string to a folder to write the output file. The file
            will be written to the current folder if not provided.
        layer_names: A list of text strings representing the layer names in vtk output.
    
    Returns:
        A text string containing the path to the index.json file.
    """
    datasets = []

    for layer_name in layer_names:

        # Set opacity for Apertures
        if layer_name == 'Aperture':
            opacity = 0.5
        else:
            opacity = 1
        
        template = copy.deepcopy(dataset_template)
        template['name'] = layer_name
        template['httpDataSetReader']['url'] = layer_name
        template['property']['diffuseColor'] = layer_colors[layer_name]
        template['property']['opacity'] = opacity

        datasets.append(template)

    index = copy.deepcopy(index_template)
    index['scene'] = datasets
    
    file_path = os.path.join(target_folder, 'index.json')

    with open(file_path, 'w') as fp:
        json.dump(index, fp)

    return file_path
