'''
Routines for parsing and loading job specification files.
'''
import os.path
from datetime import timedelta
import yaml
from ..utils.io import pkg_config_dir
from ..utils.time import get_latest_date

def load_rshrfmatlab_spec(version='latest'):
    '''
    Leverages built in configuration from yaml file
    :return: dictionary with run parameters
    '''
    with open(os.path.join(pkg_config_dir(), 'rshrfmatlab_versions.yml'),'r') as file:
        spec_versions = yaml.load(file, Loader=yaml.FullLoader)

    if version == 'latest':
        version = get_latest_date(spec_versions['versions'].keys())

    return load_job_spec(os.path.join(pkg_config_dir(), spec_versions['versions'][version]))

def load_job_spec(spec_file):
    '''
    Read job-specific globals from a pre-configured YAML file
    :param spec_file: path to YAML file to read
    :return: dictionary with specification
    '''
    with open(spec_file,'r') as file:
        spec_dict = yaml.load(file, Loader=yaml.FullLoader)

    # parse times into timedeltas
    spec_dict = {k:(timedelta(**v) if 'time' in k else v) for (k, v) in spec_dict.items()}

    return spec_dict