"""
Some utilities for debugging in the iPython console...
"""


def setup_environment_rshrf():
    from slurmhelper.specs import load_builtin_spec
    from ..utils.io import calculate_directories

    config = load_builtin_spec("rshrfmatlab", "2022-03-16")
    paths = calculate_directories("/tmp", config["base_directory_name"])
    job_list = [1, 2, 3]

    pass
