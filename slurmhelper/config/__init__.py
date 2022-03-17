'''
Routines for parsing and loading job specification files.
'''
import os
from pathlib import Path
from datetime import timedelta
import yaml
from ..utils.io import pkg_config_dir
from ..utils.misc import unique
from ..utils.time import get_latest_date, datetime_valid

def get_builtin_specs():
    '''
    Produces a list of all available specs
    :return:
    '''

    # get list of available dicts, assuming the _ separates name_version
    specs = [s.stem.split('_') for s in Path(pkg_config_dir()).glob('*.yml')]

    # gives us list of tuples with valid combinations
    valid_specs = [(s[0],s[1]) for s in specs]

    # for identifying latest spec:
    spec_names = unique([l[0] for l in specs])
    spec_dict = {name:{'versions':[]} for name in spec_names}
    for spec in specs:
        spec_dict[spec[0]]['versions'].append(spec[1])

    # identify latest version for a given spec
    for spec in spec_dict.keys():
        if True in list(map(datetime_valid, spec_dict[spec]['versions'])):
            # get max from files with datetimes
            dates = list(filter(datetime_valid, spec_dict[spec]['versions']))
            spec_dict[spec]['latest'] = get_latest_date(dates)

    print(spec_dict)

    return spec_dict

def load_builtin_spec(spec_tuple):
    '''
    Leverages built in configuration from yaml file
    :param spec_tuple: tuple with format (specname, specversion). E.g., for rshrfmatlab_2021-06-01.yml, should be
    ('rshrfmatlab','2021-06-01').
    :return: dictionary with run parameters
    '''
    spec, ver = spec_tuple
    if spec_tuple[1] == 'latest':
        valid_specs, latest_versions = get_builtin_specs()
        ver = latest_versions[spec]
    yml_name = f'{spec}_{ver}.yml'
    return load_job_spec(os.path.join(pkg_config_dir(),yml_name))

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