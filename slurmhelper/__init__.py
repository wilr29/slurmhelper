"""This python module contains command line tools, classes, and other helpful things
to make your experience of running jobs in an HPC that uses slurm a little bit easier.

Submodules
==========

.. autosummary::
    :toctree: _autosummary

    cli
    config
    jobs
    utils
"""
from slurmhelper import cli, config, jobs, utils

# Versioneer: add version string
from .src._version import get_versions

__version__ = get_versions()["version"]
del get_versions
