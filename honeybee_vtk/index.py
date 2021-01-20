"""Write index.json to color vtk datasets."""

import os
import json

# Scarlet colors in decimal
layer_colors = {
    'Wall': [0.858, 0.713, 0.560],
    'Aperture': [0.858, 0.988, 1],
    'Door': [0.776, 0.847, 0.686],
    'Shade': [0.937, 0.643, 0.545],
    'Floor': [0.031, 0.572, 0.647],
    'RoofCeiling': [0.407, 0.325, 0.411],
    'Aperture vectors': [1, 1, 1],
    'grid base': [0.925, 0.250, 0.403],
    'grid base vectors': [1, 1, 1],
    'grid mesh' : [0.925, 0.250, 0.403],
    'grid mesh vectors': [1, 1, 1],
    'AirBoundary': [0.109, 0.227, 0.074],
    'Context': [0.925, 0.305, 0.125],
    'grid points': [0.925, 0.250, 0.403],
    'grid points vectors': [1, 1, 1]
}



def write_index_json(target_folder, layer_names):
    """write_index_json [summary]

    Args:
        target_folder: A text string to a folder to write the output file. The file
            will be written to the current folder if not provided.
        layer_names: A list of text strings representing the layer names in vtk output.
    
    Returns:
        A text string containing the path to the index.json file.
    """
    # index.json template
    index = {
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

    datasets = []
    for layer_name in layer_names:
        # Dataset template to be modified
        dataset_template = {
            "name": "Wall.vtk",
            "type": "httpDataSetReader",
            "httpDataSetReader": {"url": "Wall"},
            "actor": {
                "origin": [0, 0, 0],
                "scale": [1, 1, 1],
                "position": [0, 0, 0]
            },
            "actorRotation": [0, 0, 0, 1],
            "mapper": {
                "colorByArrayName": "",
                "colorMode": 1,
                "scalarMode": 0
            },
            "property": {
                "representation": 2,
                "edgeVisibility": 0,
                "diffuseColor": [0.858824, 0.713725, 0.560784],
                "pointSize": 5,
                "opacity": 1
            }
            }
        dataset_template['name'] = layer_name
        dataset_template['httpDataSetReader']['url'] = layer_name
        dataset_template['property']['diffuseColor'] = layer_colors[layer_name]
        datasets.append(dataset_template)
    
    index['scene'] = datasets
    
    file_path = os.path.join(target_folder, 'index.json')

    with open(file_path, 'w') as fp:
        json.dump(index, fp)

    return file_path