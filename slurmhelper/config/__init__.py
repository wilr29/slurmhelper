import os.path

import yaml
from ..utils.io import pkg_config_dir
from datetime import timedelta

def load_rshrfmatlab_spec():
    '''
    Leverages built in configuration from yaml file
    :return: dictionary with run parameters
    '''
    return load_job_spec(os.path.join(pkg_config_dir(), 'rshrfmatlab.yml'))

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