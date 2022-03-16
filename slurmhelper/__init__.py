from slurmhelper import cli, config, jobs, utils

# Versioneer: add version string
from .src._version import get_versions
__version__ = get_versions()['version']
del get_versions