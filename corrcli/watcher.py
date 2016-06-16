"""The Watcher class to launch a deamon process.
"""
import uuid
import logging
import os
import glob
import signal
import pandas
import daemon
import daemon.pidfile


class Watcher(object):
    """Launch a callback function as a daemon process.

    Multiple `Watcher`s can launch multiple callback functions as
    daemon processes and keep track of running deamons as well as
    shutdown daemons.

    Attributes:
      watcher_id: a unique ID for each watcher
      daemon_dir: the directory for pid and log files
      logging_on: whether the daemon should log its output
      log_file: the path to the deaemon's log file
      callback: the callback function that's executed in the daemon
      pidext: the extension for pid files

    Note that a possible alternative to this class might be
    http://python-service.readthedocs.io/en/latest/.
    """
    pidext = 'pid'
    def __init__(self, callback, config_dir, logging_on=False):
        """Instantiate a `Watcher`.

        Args:
          callback: the callback function that's executed in the
            daemon
          config_dir: the CoRR config directory
          logging_on: whether the daemon should log its output

        """
        self.watcher_id = uuid.uuid4()
        self.daemon_dir = self.get_daemon_dir(config_dir)
        if not os.path.exists(self.daemon_dir):
            os.makedirs(self.daemon_dir)
        self.logging_on = logging_on
        self.log_file = os.path.join(self.daemon_dir, '{0}_daemon.log'.format(self.watcher_id))
        self.callback = callback

    @staticmethod
    def get_daemon_dir(config_dir):
        """Get the daemon directory.

        Args:
          config_dir: the CoRR config directory

        Returns:
          A path like `/home/user/.config/corrcli/corr_daemons`.
        """
        return os.path.join(config_dir, 'corr_daemons')

    def get_pidfile(self):
        """Get the PID file for the daemon process.

        The file is named something like
        `e6f14ae7-efef-435e-b9ce-db04982afc5c.pid`.

        Returns:
           a PIDLockFile instance
        """
        lock_file = os.path.join(self.daemon_dir,
                                 '{0}.{1}'.format(self.watcher_id, self.pidext))
        return daemon.pidfile.PIDLockFile(lock_file)

    def get_logger(self):
        """Get the logger for logging the deamon process.

        Returns:
          a tuple containing the logger and the file handler
        """
        logger = logging.getLogger("CoRR Watcher Log -- {0}".format(self.watcher_id))
        logger.setLevel(level=logging.INFO)
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
        with daemon_context:
            self._run(logger, daemon_context)

    @classmethod
    def stop(cls, config_dir, watcher_ids=(), all_watchers=False):
        """Stop daemon processes base on watcher_ids.

        Args:
          config_dir: the CoRR config directory
          watcher_ids: the watcher IDs to stop
          all_watchers: shut down all daemons

        Returns:
          a data frame containing the watcher IDs and PIDs for all
          daemons shutdown

        """
        watcher_df = cls.list(config_dir)
        if all_watchers:
            rows_df = watcher_df
        else:
            rows_df = watcher_df.loc[watcher_df['watcher_id'].isin(watcher_ids)]

        for _, row in rows_df.iterrows():
            os.kill(row.process_id, signal.SIGTERM)

        return rows_df

    @classmethod
    def list(cls, config_dir):
        """List all running daemons.

        Args:
          config_dir: the CoRR config directory

        Returns:
          a data frame containing the watcher IDs and PIDs for all
          running daemons
        """
        daemon_dir = cls.get_daemon_dir(config_dir)
        pidfile_regex = os.path.join(daemon_dir, '*.{0}'.format(cls.pidext))
        watcher_ids = []
        pids = []
        for pidfile in glob.glob(pidfile_regex):
            with open(pidfile, 'r') as fpointer:
                pids.append(int(fpointer.read()))
            watcher_id = os.path.splitext(os.path.split(pidfile)[1])[0]
            watcher_ids.append(watcher_id)
        return pandas.DataFrame({'watcher_id' : watcher_ids,
                                 'process_id' : pids})


    def _run(self, logger, context):
        pid = context.pidfile.read_pid()
        if logger:
            logger.info("Start watcher with pid {0}".format(pid))
        self.callback(logger=logger)
        if logger:
            logger.info("Stop watcher with pid {1}".format(pid))
