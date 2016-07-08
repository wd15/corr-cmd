"""The CoRRDaemon class to launch a deamon process.
"""
import uuid
import logging
import os
import glob
import signal
from subprocess import Popen
from time import sleep
from contextlib import contextmanager

import pandas
import daemon
import daemon.pidfile

from .commands.cli import DEFAULT_DAEMON_DIR


class CoRRDaemon(object):
    """Launch a callback function as a daemon process.

    Multiple `CoRRDaemon`s can launch multiple callback functions as
    daemon processes and keep track of running deamons as well as
    shutdown daemons.

    Attributes:
      daemon_id: a unique ID for each daemon
      daemon_dir: the directory for pid and log files
      logging_on: whether the daemon should log its output
      log_file: the path to the deaemon's log file
      callback: the callback function that's executed in the daemon
      pidext: the extension for pid files

    Note that a possible alternative to this class might be
    http://python-service.readthedocs.io/en/latest/.

    """
    pidext = 'pid'
    def __init__(self, callback, config_dir, daemon_on, logging_on=False):
        """Instantiate a `CoRRDaemon`.

        Args:
          callback: the callback function that's executed in the
            daemon
          config_dir: the CoRR config directory
          logging_on: whether the daemon should log its output

        """
        self.daemon_id = str(uuid.uuid4().hex)[:12]
        self.daemon_dir = self.get_daemon_dir(config_dir)
        if not os.path.exists(self.daemon_dir):
            os.makedirs(self.daemon_dir)
        self.logging_on = logging_on
        self.log_file = os.path.join(self.daemon_dir, '{0}.log'.format(self.daemon_id))
        self.callback = callback
        self.config_dir = config_dir
        self.daemon_on = daemon_on

    @staticmethod
    def get_daemon_dir(config_dir):
        """Get the daemon directory.

        Args:
          config_dir: the CoRR config directory

        Returns:
          A path like `/home/user/.config/corrcli/daemons`.
        """
        return os.path.join(config_dir, DEFAULT_DAEMON_DIR)

    def get_pidfile(self):
        """Get the PID file for the daemon process.

        The file is named something like
        `e6f14ae7-efef-435e-b9ce-db04982afc5c.pid`.

        Returns:
           a PIDLockFile instance
        """
        lock_file = os.path.join(self.daemon_dir,
                                 '{0}.{1}'.format(self.daemon_id, self.pidext))
        return daemon.pidfile.PIDLockFile(lock_file)

    def get_logger(self):
        """Get the logger for logging the deamon process.

        Returns:
          a tuple containing the logger and the file handler
        """
        logger = logging.getLogger("CoRRDaemon Log -- {0}".format(self.daemon_id))
        logger.setLevel(level=logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler = logging.FileHandler(self.log_file)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger, handler

    def start(self):
        """Start a process and detach as a daemon.
        """
        files_preserve = []
        logger = None
        if self.logging_on:
            logger, handler = self.get_logger()
            files_preserve.append(handler.stream)

        daemon_context = daemon.DaemonContext(pidfile=self.get_pidfile(),
                                              files_preserve=files_preserve)
        if self.daemon_on:
            with daemon_context:
                self._run(logger, daemon_context)
        else:
            self._run(logger, daemon_context)

    @classmethod
    def stop(cls, config_dir, daemon_ids=(), all_daemons=False):
        """Stop daemon processes base on daemon_ids.

        Args:
          config_dir: the CoRR config directory
          daemon_ids: the daemon IDs to stop
          all_daemons: shut down all daemons

        Returns:
          a data frame containing the daemon IDs and PIDs for all
          daemons shutdown

        """
        daemon_df = cls.list(config_dir)
        if all_daemons:
            rows_df = daemon_df
        else:
            rows_df = daemon_df.loc[daemon_df['daemon_id'].isin(daemon_ids)]

        for _, row in rows_df.iterrows():
            os.kill(row.process_id, signal.SIGTERM)

        return rows_df

    @classmethod
    def list(cls, config_dir):
        """List all running daemons.

        Args:
          config_dir: the CoRR config directory

        Returns:
          a data frame containing the deamon IDs and PIDs for all
          running daemons
        """
        daemon_dir = cls.get_daemon_dir(config_dir)
        pidfile_regex = os.path.join(daemon_dir, '*.{0}'.format(cls.pidext))
        daemon_ids = []
        pids = []
        for pidfile in glob.glob(pidfile_regex):
            with open(pidfile, 'r') as fpointer:
                pids.append(int(fpointer.read()))
            daemon_id = os.path.splitext(os.path.split(pidfile)[1])[0]
            daemon_ids.append(daemon_id)
        return pandas.DataFrame({'daemon_id' : daemon_ids,
                                 'process_id' : pids})

    def _run(self, logger, context):
        pid = context.pidfile.read_pid()
        if logger:
            logger.info("Start daemon with pid {0}".format(pid))
        try:
            self.callback(self.daemon_id, self.config_dir, logger=logger)
        except Exception:
            if logger:
                logger.exception("Exception in daemon callback function.")
            raise

        if logger:
            logger.info("Stop daemon with pid {0}".format(pid))


@contextmanager
def start_daemon(config_dir, callback_func=None):
    """CoRR Daemon context manager.

    Only used for tests.

    Args:
      config_dir: the CoRR configuration directory
      callback_func: the name of the callback function

    Yields:
      the daemon ID

    """
    daemon_ids_before = set(CoRRDaemon.list(config_dir).daemon_id)
    arguments = ['corrcli',
                 '--config-dir={0}'.format(config_dir),
                 'watch',
                 'start',
                 '--log']
    if callback_func is not None:
        arguments.append('--callback-func={0}'.format(callback_func))
    Popen(arguments).communicate()
    sleep(1)
    daemon_id = (set(CoRRDaemon.list(config_dir).daemon_id) - daemon_ids_before).pop()
    yield daemon_id
    arguments = ['corrcli',
                 '--config-dir={0}'.format(config_dir),
                 'watch',
                 'stop',
                 '{0}'.format(daemon_id)]
    Popen(arguments).communicate()
