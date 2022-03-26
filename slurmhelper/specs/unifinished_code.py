"""
Module for handling spec-related stuff.
"""
import os
from datetime import timedelta

import yaml

# TODO: I would ideally like to leverage the Cerberus package to
#       validate schema stuff. But alas, that is for a later time...

# Required keys that must be indicated for any spec
spec_required_keys = {
    "spec_name",
    "spec_version",
    "header",
    "run_script",
    "database",
    "output_path",
    "job_time",
    "max_job_time",
}

# Optional keys. Not needed for a spec, but allowed.
spec_optional_keys = {
    "preamble",
    "array_footer",
    "script_global_settings",
    "copy_script",
    "clean_script",
    "output_path_subject",
    "output_path_subject_expr",
    "base_directory_name",
    "job_ramp_up_time",
    "expected_n_files",
    "compute_function",
}


class JobSpec:
    def __init__(self, yaml_file):

        self._spec_dict = self.load_job_spec(yaml_file)
        self.validate_spec()

    def load_job_spec(spec_file):
        """
        Read job-specific globals from a pre-configured YAML file
        :param spec_file: path to YAML file to read
        :return: dictionary with specification
        """
        if not os.path.exists(spec_file):
            raise AssertionError(f"{spec_file} does not exist!")

        try:
            with open(spec_file, "r") as file:
                spec_dict = yaml.load(file, Loader=yaml.FullLoader)
        except:
            raise ValueError(f"Error loading {spec_file}. Is this a valid YAML file?")

        # parse time variables into timedeltas
        spec_dict = {
            k: (timedelta(**v) if "time" in k else v) for (k, v) in spec_dict.items()
        }

        return spec_dict

    def validate_spec(self):
        spec = self._spec_dict
        # ensure all mandatory keys are present
        # works b/c set math: {a, b, c} - {a, b, c, x, y, z} should == {}
        if len(spec_required_keys - spec.keys()) != 0:
            raise AssertionError(
                f"Some required keys are not "
                f"defined in your spec. these are: "
                f"{' '.join(list(spec_required_keys - spec.keys()))}"
            )
        # warn user if optional keys that are not defined were include
        # if (len(spec_required_keys.union(spec_optional_keys) - spec.keys()) > 0):
        #    logging.warn('Variables ;...')

    def __str__(self):
        pass
