"""Command to write a config file to be consumed by honeybee-vtk."""
import click
import json
import sys
import traceback
import pathlib
from honeybee_vtk.config import DataConfig, Config, InputFile


@click.group()
def config():
    """Honeybee-vtk command to write a config file."""
    pass


@config.command('config')
@click.argument('input-file', type=click.Path(exists=True, dir_okay=True,
                                              resolve_path=True), required=True)
@click.option('--folder-path', '-fp',
              type=click.Path(dir_okay=True, resolve_path=True),
              default='.', show_default=True,
              help='Path to the folder where the config file shall be written.')
@click.option('--name', '-n', type=click.STRING, default='config',
              show_default=True, help='Name of the config file.')
def config(input_file, folder_path, name):
    """Write a config file to be consumed by honeybee-vtk.

    \b
    Args:
        input_file: A path to the input file in json format.
        folder_path: Path to the folder where the config file shall be written.
            Defaults to the current working directory.
        name: A string as the name of the config file. Defaults to 'config'.
    """
    try:
        with open(input_file) as fh:
            input = json.load(fh)
    except json.decoder.JSONDecodeError:
        raise TypeError(
            'Not a valid json file.'
        )
    else:
        input = InputFile.parse_obj(input).dict()
        try:
            req_data = []
            for count, path in enumerate(input['paths']):
                temp = {}
                temp['identifier'] = input['identifiers'][count]
                temp['object_type'] = 'grid'
                temp['unit'] = input['units'][count]
                temp['path'] = path
                req_data.append(temp)

            data_configs = [DataConfig.parse_obj(data) for data in req_data]
            config_data = {'data': data_configs}
            config = Config.parse_obj(config_data)

            file_name = f'{name}.json'
            target_path = pathlib.Path(folder_path)
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
