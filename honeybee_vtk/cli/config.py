"""Command to write a config file to be consumed by honeybee-vtk."""
import click
import pathlib
from honeybee_vtk.config import DataConfig


@click.group()
def config():
    """Honeybee-vtk command to write a config file."""
    pass


@config.command('config')
@click.argument('paths',
                type=click.Path(exists=True, dir_okay=True, resolve_path=True),
                nargs=-1, required=True)
@click.option('--id', type=click.STRING, required=True, multiple=True,
              help='identifier given to the data. For example, "Daylight-Factor".')
@click.option('--unit', type=click.STRING, required=True, multiple=True,
              help='The unit of the data being loaded.')
@click.option('--config-path', '-cp',
              type=click.Path(exists=True, dir_okay=True, resolve_path=True),
              default=pathlib.Path.cwd(), show_default=True,
              help='Path to where the config file shall be written.')
@click.option('--name', '-n', type=click.STRING, default='config', show_default=True,
              help='Name of the config file.')
def config(paths, id, unit, config_path, name,):
    """Write a config file to be consumed by honeybee-vtk.

    \b
    Args:
        paths: Valid paths to results folders. Accepts multiple values.
        id: A string to be used as identifier for the data being mounted on the
            model. For example, "Daylight-Factor". Accepts multiple values.
        unit: A string representing the unit of the data being mounted on the model.
            For example, 'Lux'. Accepts multiple values.
        config_path: Path to where the config file shall be written..
            Defaults to the current working directory.
        name: A string as the name of the config file. Defaults to 'config'.
    """
    if not len(paths) == len(id) == len(unit):
        raise ValueError(
            'id and unit option on this command accepts multiple values. Make sure'
            ' to provide the number of values in options "id" and "unit" to match the'
            f' {len(paths)} number of paths provided as an argument to the command.'
        )

    print(paths)
    print(config_path)
    print(name)
    print(id)
    print(unit)
