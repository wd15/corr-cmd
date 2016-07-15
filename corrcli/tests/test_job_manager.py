"""Test the command line tool.
"""
import os
from subprocess import Popen
from time import sleep

from click.testing import CliRunner

from corrcli.commands.cli import DEFAULT_WRITE_REFRESH_RATE
from corrcli.stores.file_store import FileStore
from corrcli.watcher import start_watcher


def configure(config_dir, refresh_rate):
    """Configure CoRR

    """
    arguments = ['corrcli',
                 '--config-dir={0}'.format(config_dir),
                 'config',
                 'set',
                 '--email=test@test.com',
                 '--author="Test Person"',
                 '--write-refresh-rate={0}'.format(refresh_rate)]
    Popen(arguments).communicate()
    sleep(3)

def start_process(watcher_id, config_dir):
    """Launch a test process.

    """
    contents = """
import time
while True:
    time.sleep(10.0)
"""
    test_process_file = os.path.join(config_dir, 'test_process.py')
    with open(test_process_file, 'w') as fout:
        fout.write(contents)
    arguments = ['python',
                 test_process_file,
                 watcher_id]
    process = Popen(arguments)
    return process

def test_job_manager():
    """Test that jobs can be captured.
    """
    write_refresh_rate = 1
    runner = CliRunner()
    with runner.isolated_filesystem() as config_path:
        configure(config_path, write_refresh_rate)
        with start_watcher(config_path) as (watcher_id, _):
            try:
                process = start_process(watcher_id, config_path)
                sleep(write_refresh_rate + 1)
                jobs = FileStore.read_all(config_path)
            except: # pragma: no cover
                process.kill()
                raise
            process.kill()
            assert len(jobs) == 1
            assert jobs[0]['status'] != 'finished'
            sleep(write_refresh_rate + 1)
            jobs = FileStore.read_all(config_path)
            assert len(jobs) == 1
            assert jobs[0]['status'] == 'zombie'


def test_noconfig():
    """Test that jobs are captured when no config set.
    """
    runner = CliRunner()
    with runner.isolated_filesystem() as config_path:
        with start_watcher(config_path) as (watcher_id, _):
            try:
                process = start_process(watcher_id, config_path)
                sleep(DEFAULT_WRITE_REFRESH_RATE * 2)
                jobs = FileStore.read_all(config_path)
            except: # pragma: no cover
                process.kill()
                raise
            process.kill()
            assert len(jobs) == 1
            assert jobs[0]['status'] != 'finished'
