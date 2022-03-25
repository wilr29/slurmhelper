"""
Functions used to aid in reporting information to the user about runs, jobs, etc.
"""

import glob
import logging
import os
import re
import time
import subprocess
from pathlib import Path
from io import StringIO
from pprint import pprint
import cmd

import pandas as pd

from ..jobs.classes import TestableJob
from ..jobs.utils import build_job_objects

logger = logging.getLogger("cli")


def list_slurm(dirs):
    """
    Helpful function, prints out existing scripts in the directory structure for
    the user to review and such.
    :param dirs: dict output of calculate_directories()
    :return:
    """
    sbatch_files = glob.glob(os.path.join(dirs["slurm_scripts"], "sb-????.sh"))
    found_sbatch = [re.search("sb-(.+?).sh", x).group(1) for x in sbatch_files]
    found_sbatch.sort()
    if not found_sbatch:
        raise Exception(
            "No valid sbatch scripts found in your directory... whats up with that???"
        )
    else:
        print(
            "{num_sbatch} sbatch submission scripts found.".format(
                num_sbatch=len(found_sbatch)
            )
        )
        print("These scripts have the following ids:")
        print(found_sbatch)

    # now check for arrays
    sbatch_arrays = glob.glob(os.path.join(dirs["slurm_scripts"], "sb-????-???.sh"))
    found_arrays = [re.search("sb-(.+?).sh", x).group(1) for x in sbatch_arrays]
    if not found_arrays:
        print("No job arrays found.")
    else:
        split = [x.split("-") for x in found_arrays]
        array_info = dict()
        for script in split:
            if script[0] not in array_info.keys():
                array_info[script[0]] = [script[1]]
            else:
                array_info[script[0]].append(script[1])
        # now print stuff
        print("Of these, {num_arrays} are slurm arrays. See below for details:")
        for key in array_info.keys():
            print(
                "ID: {sbatch_id}, array of length {array_length}. Includes jobs: ".format(
                    sbatch_id=key, array_length=len(array_info[key])
                )
            )
            print(array_info[key])

    return


def check_queue():
    # assumes slurm
    out = subprocess.check_output(
        ["squeue", "-u", os.environ["USER"]], encoding="UTF-8"
    )
    df = pd.read_fwf(StringIO(out))
    # TODO: merge this with info on sbatch thingys, then do some magic to make it more informative!
    pprint(df)


def pretty_print_job_ids(ids_list, n_cols=5):
    chunks = [ids_list[x : x + n_cols] for x in range(0, len(ids_list), n_cols)]
    print("\n".join(["\t".join([str(cell) for cell in row]) for row in chunks]))


def check_completed(
    dirs, config, job_list=None, return_completed_list=False, failed_report=False
):
    # if job list is none, assume all of them are the ones we care about...
    # basically copypaste from check_runtimes

    logger.info(f"Building job objects...")
    job_obj_list = build_job_objects(dirs, config, job_list)

    with_logs = list(filter(lambda x: x.has_job_log, job_obj_list))

    if return_completed_list and len(with_logs) < len(job_obj_list):
        logger.warning(
            f"Of the {len(job_obj_list)} total job ids considered,"
            f"only {len(with_logs)} of those have valid log files."
        )

    with_success = list(filter(lambda x: x.ran_successfully, with_logs))

    if return_completed_list and len(with_logs) < len(job_list):
        logger.warning(
            f"Of the {len(with_logs)} jobs with logs, only "
            f"{len(with_success)} appear to have completed successfully."
        )

    # Now print stuff nicely.

    if return_completed_list:
        rv = with_success
    else:
        rv = None
        no_logs_ids = list(
            set([str(job) for job in job_obj_list])
            - set([str(job) for job in with_logs])
        )
        failed_job_ids = list(
            set([str(job) for job in with_logs])
            - set([str(job) for job in with_success])
        )
        print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        print("~ slurmhelper check completed: results ~~~~~~~~")
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
        print(f"jobs considered: {len(job_obj_list)}")
        print(
            f"logs exist in logs/jobs/<order_id>.txt: {len(with_logs)} ({len(with_logs)*100/len(job_obj_list)}% of considered)"
        )
        print(f"logs indicate success: {len(with_success)}")
        print(f"    ({len(with_success)*100/len(job_obj_list)}% of considered);")
        print(
            f"    ({len(with_success)*100/len(with_logs)}% of considered w/ existing logs);"
        )
        if len(no_logs_ids) > 0:
            print(f"\njobs without logfiles (n = {len(no_logs_ids)})")
            pretty_print_job_ids(no_logs_ids)
        if len(failed_job_ids) > 0:
            print(f"\nfailed jobs (n = {len(failed_job_ids)}):")
            pretty_print_job_ids(failed_job_ids)

            if failed_report:
                print("~~~~~~ job logs ~~~~~~~")
                failed_jobs = list(
                    filter(lambda x: str(x) in failed_job_ids, with_logs)
                )
                for job in failed_jobs:
                    job.print_job_log()
            else:
                print(
                    "\nTip: rerun with --show-failed-logs flag to print out job logs available for failed jobs\n"
                )

    return rv


def check_runtimes(dirs, config, job_list=None):
    # assumptions about runtime: formatting, position
    # runtime_unit = seconds
    runtime_unit = "seconds"
    runtime_line_position = -3
    runtime_strip_str = "runtime: "

    with_success = check_completed(
        dirs, config, job_list, failed_report=False, return_completed_list=True
    )

    runtimes = []
    for job in with_success:
        lines = job.read_job_log_lines()
        rt = int(lines[runtime_line_position].strip(runtime_strip_str))
        runtimes.append(rt)

    runtime_df = pd.DataFrame(
        pd.to_timedelta(runtimes, unit=runtime_unit), columns=["runtime"]
    )
    # print out descriptive stats! :)
    print(runtime_df.describe(percentiles=[0.25, 0.5, 0.75, 0.90, 0.95]))


def check_runs(job_list, dirs, args, config):
    """
    Conducts various checks on a given set of jobs, as defined in the
    job class.
    :param job_list: list of jobs to check
    :param dirs: directory dictionary, as produced by .io:compute_directories()
    :param args: args from the arg parser
    :param config: config parameter dictionary
    :return:
    """
    if len(job_list) < 1:
        raise ValueError("Job list length should be greater than 0")

    if args.verbose:
        print("loading database....")

    # assumption, we use the database specified as a global earlier in the script
    db_filepath = Path(dirs["base"]).joinpath("db.csv")
    if db_filepath.exists():
        db = pd.read_csv(db_filepath)
    else:
        raise (
            FileNotFoundError,
            "Database file db.csv is missing from your working directory!",
        )
    db.sort_values("order_id")  # ensure they're sorted properly

    # calculate a globbing expression to check for outputs
    sfmt_glob = config["output_path_subject_expr"].format
    db["glob_output_expr"] = db.apply(lambda x: sfmt_glob(**x), 1)

    sfmt_dir = os.path.join(
        config["output_path"], *config["output_path_subject"]
    ).format
    db["output_dir"] = db.apply(lambda x: sfmt_dir(**x), 1)

    job_tests = [TestableJob(db, dirs, job, config) for job in job_list]
    rows = [job_test.get_results_dict() for job_test in job_tests]
    out_db = pd.DataFrame.from_records(rows)
    out_db.sort_values("order_id")

    valid = out_db.loc[out_db["valid"], "order_id"].values.tolist()
    not_valid = out_db.loc[out_db["valid"] == False, "order_id"].values.tolist()

    if len(valid) > 0:
        print("{num} valid jobs found.".format(num=len(valid)))
        if args.verbose:
            print("these jobs are:")
            print(valid)
    else:
        print("No valid jobs found :(")

    if len(not_valid) > 0:
        print("{num} NOT VALID / FLAGGED jobs found.".format(num=len(not_valid)))
        print("these jobs are:")
        print(not_valid)
    else:
        print("No flagged/invalid jobs! YAY :)")

    filename = "check_{timestamp}.csv".format(timestamp=time.strftime("%Y%m%d-%H%M%S"))
    out_file_path = os.path.join(dirs["checks"], filename)
    out_db.to_csv(out_file_path, index=False)
    print("Full results saved to to {filename}".format(filename=out_file_path))

    return
