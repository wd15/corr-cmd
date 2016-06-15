import click
import os


def get_version():
    """Get the version of the code from egg_info.

    Returns:
      the package version number
    """
    from pkg_resources import get_distribution, DistributionNotFound

    try:
        version = get_distribution(__name__.split('.')[0]).version # pylint: disable=no-member
    except DistributionNotFound:
        version = "unknown, try running `python setup.py egg_info`"

    return version

def get_config_dir(app_name):
    """Get the path to CoRR's config directory

    The path is platform independent.

    Args:
      app_name: name of the app

    Returns:
      the path to the config directory
    """
    config_dir = click.get_app_dir(app_name)
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    return config_dir