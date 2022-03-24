import os
import shutil
import logging

from argparse import ArgumentError
from pprint import pprint

import numpy as np
import pandas as pd

from .parser import build_parser
from .parser import valid_specs
from ..config import load_builtin_spec, load_job_spec
from ..jobs import prep_job, prep_job_array, generate_run_scripts
from ..utils.io import (
    calculate_directories,
    calculate_directories_midwayscratch,
    copy_or_clean,
    initialize_directories,
    is_valid_db,
)
from ..utils.reporting import list_slurm, check_runs


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

        log_format = "[%(levelname)s] - %(message)s"
        # set verbosity based on arguments!
        if args.verbose:
            logging.basicConfig(level=20, format=log_format)  # info
        elif args.debug:
            logging.basicConfig(level=10, format=log_format)  # debug
        else:
            logging.basicConfig(level=30, format=log_format)  # warning

        self.logger = logging.getLogger("cli")

        # A manual check - need user id if using midway
        if args.cluster == "midway2-scratch" and args.userid is None:
            raise ArgumentError(
                "If you are using midway2-scratch, you must provide your user ID!"
            )

        print(f"Slurmhelper will run the {args.operation} operation.")
        self.logger.info("Arguments specified:")
        self.logger.info(args)

        # Load spec
        if args.spec_file is not None:
            self.config = load_job_spec(args.spec_file)
            if args.verbose:
                self.logger.info(
                    f"Loaded user-given specification from {args.spec_file}"
                )
        else:
            to_load = args.spec_builtin[0].split(":")
            spec = to_load[0]
            if len(to_load) == 1:
                version = valid_specs[spec]["latest"]
            else:
                version = to_load[1]
            self.config = load_builtin_spec(spec, version)
            if args.verbose:
                self.logger.info(
                    f"Loaded built-in job specification: {spec} version {version}"
                )

        # Calculate directories
        if "base_directory_name" not in self.config.keys():
            self.logger.warning(
                "Base working dir name not specified in your spec; using default ('working')"
            )
            base_dir_name = "working"
        else:
            base_dir_name = self.config["base_directory_name"]

        # paths!
        if args.cluster is not None:
            if args.cluster[0] == "midway2-scratch":
                self.paths = calculate_directories_midwayscratch(
                    args.userid[0], base_dir_name
                )
        else:
            self.paths = calculate_directories(args.wd_path[0], base_dir_name)

        self.logger.info("Directory tree generated:")
        if args.verbose or args.debug:
            pprint(self.paths)

        # Compile job list, if required
        if not (
            (args.operation in {"list", "init"})
            or (
                args.operation == "gen-scripts"
                and args.ids is None
                and args.range is None
            )
        ):

            # load database thingy
            self.__load_database()
            # get valid job ids:
            self.__valid_ids = set(self.db.order_id.values.tolist())

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

            self.logger.info("\nThese jobs are:")
            self.logger.info(self.job_list)

            # Leverage DB to ensure job ids provided do not exceed range, or are invalid in some other way!
            assert set(self.job_list).issubset(self.__valid_ids), (
                f"Some job ids provided are not in the scope of "
                f"the csv database we are using. These are: "
                f"{set(self.job_list) - self.__valid_ids}"
            )

        # run my operation! :)
        operation = getattr(self, args.operation.replace("-", "_"))
        operation()

    def init(self):
        initialize_directories(self.paths)
        self.__validate_and_copy_db(self.args.db[0])
        print("Directory initialization concluded.")
        if self.args.full:
            print("The --full flag was used, so scripts will now be generated.")
            self.gen_scripts()  # generate template scripts for all jobs

    def list(self):
        list_slurm(self.paths)

    def gen_scripts(self):
        if hasattr(self, "job_list"):
            generate_run_scripts(self.paths, self.config, self.args, self.job_list)
        else:
            generate_run_scripts(self.paths, self.config, self.args)
        print("Script generation operation concluded.")

    def copy(self):
        copy_or_clean(self.job_list, "copy", self.paths["job_scripts"])

    def clean(self):
        copy_or_clean(self.job_list, "clean", self.paths["job_scripts"])

    def reset(self):
        self.logger.info("Will clean first, and copy next!")

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

    def validate_spec(self):
        # Not yet implemented.
        self.logger.critical("Not yet implemented.")

    def __load_database(self):
        self.db = pd.read_csv(os.path.join(self.paths["base"], "db.csv"))

    def __validate_and_copy_db(self, db_file):
        self.logger.info(f"validating file {db_file}")
        if not is_valid_db(db_file):
            raise ValueError(
                "Your DB file does not contain an order_id column. Please provide a valid db file in order"
                "to proceed."
            )
        else:
            self.logger.info("Copying file")
            shutil.copy2(db_file, os.path.join(self.paths["base"], "db.csv"))


def main():
    SlurmhelperCLI()
