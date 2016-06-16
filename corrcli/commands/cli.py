"""Base corrcli command for all subcommands.
"""
import os
import click
from ..tools import get_version
from ..tools import get_config_dir


@click.group()
@click.version_option(get_version())
@click.option('--config-dir',
              'config_dir',
              default=get_config_dir('corrcli'),
              help="Set the config directory for CoRR.",
              type=str)
@click.pass_context
def cli(ctx, config_dir):
    """The CoRR command line tool.
    """
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    ctx.params['config_dir'] = os.path.abspath(config_dir)
