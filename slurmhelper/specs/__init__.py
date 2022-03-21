"""
Module for handling spec-related stuff.
"""

# Required keys that must be indicated for any spec
spec_required_keys = {'spec_name', 'spec_version', 'header',
                      'run_script', 'database', 'output_path',
                      'job_time', 'max_job_time'
                      }

# Optional keys. Not needed for a spec, but allowed.
spec_optional_keys = {'preamble', 'array_footer', 'script_global_settings',
                      'copy_script', 'clean_script', 'output_path_subject',
                      'output_path_subject_expr', 'base_directory_name',
                      'job_ramp_up_time', 'expected_n_files', 'compute_function'}

class JobSpec:

    def __init__(self, yaml_file):
        pass

    def load_spec_file(self):
        pass

    def validate_spec(self):
        pass

    def __str__(self):
        pass

