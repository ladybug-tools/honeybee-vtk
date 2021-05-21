"""honeybee-vtk commands which will be added to honeybee command line interface."""

import click
from .translate import translate
from .export import export
from honeybee.cli import main

# command group for all radiance extension commands.
@click.group(help='honeybee-vtk commands.')
@click.version_option()
def vtk():
    pass


# add sub-commands to vtk
vtk.add_command(translate)
vtk.add_command(export)

main.add_command(vtk)