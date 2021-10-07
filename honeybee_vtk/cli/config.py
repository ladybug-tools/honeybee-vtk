"""Command to write a config file to be consumed by honeybee-vtk."""
import click
import sys
import traceback
import pathlib
from honeybee_vtk.config import DataConfig, Config


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
              type=click.Path(dir_okay=True, resolve_path=True),
              default=pathlib.Path.cwd(), show_default=True,
              help='Path to where the config file shall be written.')
@click.option('--name', '-n', type=click.STRING, default='config',
              show_default=True, help='Name of the config file.')
def config(paths, id, unit, config_path, name):
    """Write a config file to be consumed by honeybee-vtk.

    \b
    This command accepts multiple values. The number of values provided to the options
    "id" and "unit" must match the number of paths provided to the command as an argument.

    \b
    Args:
        paths: Valid paths to results folders. Accepts multiple values.
        id: A string to be used as identifier for the data being mounted on the
            model. For example, "Daylight-Factor". Accepts multiple values.
        unit: A string representing the unit of the data being mounted on the model.
            For example, 'Lux'. Accepts multiple values.
        config_path: Path to where the config file shall be written.
            Defaults to the current working directory.
        name: A string as the name of the config file. Defaults to 'config'.
    """
    if not len(paths) == len(id) == len(unit):
        raise ValueError(
            'id and unit option on this command accepts multiple values. Make sure'
            ' to provide the number of values in options "id" and "unit" to match the'
            f' {len(paths)} number of paths provided as an argument to the command.'
        )
    try:
        # write minimum required data required to create a DataConfig object
        req_data = []
        for count, path in enumerate(paths):
            temp = {}
            temp['identifier'] = id[count]
            temp['object_type'] = 'grid'
            temp['unit'] = unit[count]
            temp['path'] = path
            req_data.append(temp)

        data_configs = [DataConfig.parse_obj(data) for data in req_data]
        config_data = {'data': data_configs}
        config = Config.parse_obj(config_data)

        file_name = f'{name}.json'
        target_path = pathlib.Path(config_path)
        if not target_path.exists():
            target_path.mkdir()

        config_path = target_path.joinpath(file_name)
        with open(config_path, 'w') as f:
            f.write(config.json())
        output = f'Config file written to {config_path}'

    except Exception:
        traceback.print_exc()
        sys.exit(1)
    else:
        print(output, file=sys.stderr)
        return sys.exit(0)
