"""`corrcli` -- the CoRR comand line tool.

Use

    $ corrcli --help

for usage details or

    $ python setup.py install

to install and

    $ python -c "import corrcli; corrcli.test()"

to test.

"""

import os
from .tools import get_version
from .commands.cli import cli
from .commands.config import config
from .commands.watch import watch


def test(): # pragma: no cover
    r"""
    Run all the doctests available.
    """
    import pytest
    path = os.path.split(__file__)[0]
    pytest.main(args=[path, '--doctest-modules', '-r s'])


__version__ = get_version()

__all__ = ['__version__',
           'test']
