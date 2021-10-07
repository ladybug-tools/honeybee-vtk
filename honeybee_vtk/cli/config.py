import click
import pathlib


from honeybee_vtk.config import DataConfig


@click.group()
def config():
    """Honeybee-vtk command to write a config file."""
    pass


@config.command('config')
@click.argument('path',
                type=click.Path(exists=True, path_type=pathlib.Path,
                                dir_okay=True, resolve_path=True),
                nargs=-1, required=True)
@click.option('--config-path', '-cp',
              type=click.Path(exists=True, path_type=pathlib.Path,
                              dir_okay=True, resolve_path=True),
              default=pathlib.Path.cwd(), show_default=True,
              help='Path to where the config file shall be written.')
@click.option('--name', '-n', type=click.STRING, default='config', show_default=True,
              help='Name of the config file.')
@click.option('--identifier', '-id', type=click.STRING, default='Results',
              show_default=True, required=True, multiple=True,
              help='identifier given to the data. For example, "Daylight-Factor".')
@click.option('--unit', '-u', type=click.STRING, default="Unit", show_default=True,
              multiple=True, required=True, help='The unit of the data being loaded.')
@click.option('--hide', '-h', is_flag=True, default=False, show_default=True,
              multiple=True, help='A boolean switch to hide the loaded simulation data.')
def config(path, config_path, name, identifier, unit, hide):
    """Write a config file to be consumed by honeybee-vtk.

    \b
    Args:
        path: Valid paths to results folder. Accepts multiple values.
        config_path: Path to where the config file shall be written..
            Defaults to the current working directory.
        name: A string as the name of the config file. Defaults to 'config'.
        identifier: A string to be used as an identifier given to the data.
            For example, "Daylight-Factor". Accepts multiple values.
        unit: A string representing the unit of the data being loaded. For example, 'Lux'.
            Defaults to 'Unit'. Accepts multiple values.
        hide: A boolean switch to hide the loaded simulation data. Accepts multiple values.

    """
    paths = [item for item in path]
    print(paths)
    print(config_path)
    print(name)
    ids = [id for id in identifier]
    print(ids)
    units = [un for un in unit]
    print(units)
    hides = [h for h in hide]
    print(hides)
