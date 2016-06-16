"""The watch command for corrcli.

Launch a deamon that will watch for command line programs launched
with the given ID.

    $ corrcli watch start
    [ID]

Stop the deamon.

    $ corrcli watch stop [ID]

"""

import click
from ..watcher import Watcher
from .cli import cli


@cli.group()
def watch():
    """Launch a deamon for watching other processes.
    """

def test_callback(logger=None):
    """Callback function to test the daemon launcher.

    It writes to the log file and waits to be shutdown.

    Args:
      logger: a logger object to write log messages
    """
    if logger:
        logger.info("in callback function")
    from time import sleep
    while True:
        sleep(10)

@watch.command()
@click.option('--log/--no-log',
              default=False,
              help="Whether to record the output of the watcher daemon")
@click.pass_context
def start(ctx, log):
    """Launch a Daemon to watch processes.
    """
    config_dir = ctx.parent.parent.params['config_dir']
    watcher = Watcher(test_callback, config_dir, logging_on=log)
    click.echo("Launch daemon with ID: {0}".format(watcher.watcher_id))
    if log:
        click.echo("Writing logs to {0}".format(watcher.log_file))
    watcher.start()

@watch.command()
@click.option('--all', 'all_watchers', is_flag=True, help="Stop all watcher daemons.")
@click.option('--watcher-id',
              'watcher_ids',
              multiple=True,
              help="Stop the given daeomon corresping to [tag]")
@click.pass_context
def stop(ctx, all_watchers, watcher_ids):
    """Shut down watching daemons.
    """
    config_dir = ctx.parent.parent.params['config_dir']
    if (not all_watchers) and len(watcher_ids) == 0:
        click.echo("Require a watcher ID to proceed.")
    else:
        stopped_df = Watcher.stop(watcher_ids=watcher_ids,
                                  all_watchers=all_watchers,
                                  config_dir=config_dir)
        if len(stopped_df) > 0:
            click.echo("Stopping watchers.")
            for _, row in stopped_df.iterrows():
                click.echo("Stopped {0} with pid {1}".format(row.watcher_id, row.process_id))
        else:
            click.echo("No watchers stopped.")


@watch.command('list')
@click.pass_context
def list_watchers(ctx):
    """List all daemons.
    """
    config_dir = ctx.parent.parent.params['config_dir']
    watcher_df = Watcher.list(config_dir=config_dir)
    if len(watcher_df) == 0:
        click.echo("No running daemons.")
    else:
        click.echo(watcher_df.to_string(index=False))
