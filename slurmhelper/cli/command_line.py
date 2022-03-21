import numpy as np
import pandas as pd
from pprint import pprint
from argparse import ArgumentError
from .parser import build_parser
from ..utils.io import (
    calculate_directories,
    calculate_directories_midwayscratch,
    copy_or_clean,
    initialize_directories,
)
from ..utils.reporting import list_slurm, check_runs
from ..jobs import prep_job, prep_job_array, generate_run_scripts
from ..config import load_builtin_spec, load_job_spec
from .parser import valid_specs


class SlurmhelperCLI:
    """
    Command-line entrypoint class. Implements a switch to run various commands.
    """

    def __init__(self):
        # Build parser, and parse arguments
        parser = build_parser()
        args = parser.parse_args()

        # copy args to the object for easier access later on :)
        self.args = args

        # A manual check - need user id if using midway
        if args.cluster == "midway2-scratch" and args.userid is None:
            raise ArgumentError(
                "If you are using midway2-scratch, you must provide your user ID!"
            )

        print(f"Slurmhelper will run the {args.operation} operation.")
        if args.verbose:
            print("Arguments specified:")
            print(args)

        # Load spec
        if args.spec_file is not None:
            self.config = load_job_spec(args.spec_file)
            if args.verbose:
                print(f"Loaded user-given specification from {args.spec_file}")
        else:
            to_load = args.spec_builtin[0].split(":")
            spec = to_load[0]
            if len(to_load) == 1:
                version = valid_specs[spec]["latest"]
            else:
                version = to_load[1]
            self.config = load_builtin_spec(spec, version)
            if args.verbose:
                print(f"Loaded built-in job specification: {spec} version {version}")

        # load database thingy
        self.__load_database()
        # get valid job ids:
        self.__valid_ids = set(self.db.order_id.values.tolist())

        # Compile job list, if required
        if not (
            (args.operation in {"list", "init"})
            or (
                args.operation == "gen-scripts"
                and args.ids is None
                and args.range is None
            )
        ):
            self.job_list = []
            if args.ids is not None:
                self.job_list += args.ids
            else:
                self.job_list += np.arange(args.range[0], args.range[1] + 1).tolist()

            print(
                "A total of {n} jobs would be affected by this call.".format(
                    n=len(self.job_list)
                )
            )

            if args.verbose:
                print("\nThese jobs are:")
                print(self.job_list)

        # Leverage DB to ensure job ids provided do not exceed range, or are invalid in some other way!
        assert set(self.job_list).issubset(self.__valid_ids), (
            f"Some job ids provided are not in the scope of "
            f"the csv database we are using. These are: "
            f"{set(self.job_list) - self.__valid_ids}"
        )

        # Calculate directories
        if "base_directory_name" not in self.config.keys():
            print(
                "Base working dir name not specified in your spec; using default ('working')"
            )
            base_dir_name = "working"
        else:
            base_dir_name = self.config["base_directory_name"]

        if args.cluster == "midway2-scratch":
            self.paths = calculate_directories_midwayscratch(args.userid, base_dir_name)
        else:
            self.paths = calculate_directories(args.wd_path[0], base_dir_name)
        if args.verbose:
            print("Directory tree generated:")
            pprint(self.paths)

        # run my operation! :)
        operation = getattr(self, args.operation.replace("-", "_"))
        operation()

    def init(self):
        initialize_directories(self.paths)

    def list(self):
        list_slurm(self.paths)

    def gen_scripts(self):
        if hasattr(self, "job_list"):
            generate_run_scripts(self.paths, self.config, self.args, self.job_list)
        else:
            generate_run_scripts(self.paths, self.config, self.args)

    def copy(self):
        copy_or_clean(self.job_list, "copy", self.paths["job_scripts"])

    def clean(self):
        copy_or_clean(self.job_list, "clean", self.paths["job_scripts"])

    def reset(self):
        print("Will clean first, and copy next!")
        try:
            copy_or_clean(self.job_list, "clean", self.paths["job_scripts"])
            copy_or_clean(self.job_list, "copy", self.paths["job_scripts"])
        except Exception as e:
            raise e

    def prep(self):
        prep_job(self.config, self.job_list, self.paths, self.args)

    def prep_array(self):
        prep_job_array(self.config, self.job_list, self.paths, self.args)

    def check(self):
        check_runs(self.job_list, self.paths, self.args, self.config)

    def __load_database(self):
        self.db = pd.read_csv(self.config["database"])


def main():
    SlurmhelperCLI()
