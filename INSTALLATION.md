# Installing CoRR-cli

## Requirements

The requirements are outlined in [requirements.txt](requirements.txt).
Currently CoRR-cli only works on linux due to the `deamon` package
only working on linux.

## Installation

To install CoRR-cli, clone the repository and install:

    $ git clone git@github.com:usnistgov/corr-cli.git
    $ cd corr-cli
    $ python setup.py install

and test with

    $ python -c "import corrcli; corrcli.test()"
