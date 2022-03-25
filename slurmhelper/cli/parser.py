import argparse
import datetime
import os

from ..config import get_builtin_specs

valid_specs = get_builtin_specs()
valid_spec_names = valid_specs.keys()


def valid_time(x):
    # some code here drawn from https://programtalk.com/python-examples/argparse.ArgumentTypeError/?ipage=3
    if not all([t.isdigit() for t in x.split(":")]):
        raise argparse.ArgumentTypeError("Invalid time format: {}".format(x))
    print(len(x.split(":")))
    if len(x.split(":")) != 3:
        raise argparse.ArgumentTypeError(
            "Please indicate hh:mm:ss; no more, no less: you provided {}".format(x)
        )
    # Valid time (e.g. hour must be between 0..23)
    try:
        datetime.time(*map(int, x.split(":")))
    except ValueError as e:
        raise argparse.ArgumentTypeError("Invalid time format: {}".format(e))

    return x


# def wall_time_type(x):
#     """
#     Definition of a wall time type for validating in argparse.
#     :param x: list assumed to be of length 3 in order hours, minutes, seconds.
#     :return:
#     """
#     # Assertions
#     assert isinstance(x, list)
#     assert len(x) == 3
#     # Validation
#     hours = x[0]
#     minutes = x[1]
#     seconds = x[2]
#     if seconds > 59 or seconds < 0:
#         raise argparse.ArgumentTypeError("Seconds value needs to be 0 <= secs < 60")
#     elif minutes > 59 or minutes < 0:
#         raise argparse.ArgumentTypeError("Minutes value needs to be 0 <= minutes < 60")
#     elif hours > 23 or hours < 0:
#         raise argparse.ArgumentTypeError("Hours value needs to be 0 <= hours < 24")
#     return x


def built_in_spec_type(x):
    """
    Definition for valid built-in specs
    :param x: string
    :return:
    """
    # Assertions
    assert isinstance(x, str), "a string should be provided..."
    # Validation
    l = x.split(":")
    assert len(l) == 1 or len(l) == 2, (
        f"Something weird is happening when parsing your built-in spec argument. "
        f"Make sure you do not have more than one colon "
        f"present. You provided: {x}"
    )
    spec_name = l[0]
    if spec_name not in valid_specs.keys():
        raise argparse.ArgumentTypeError(
            f"The spec you indicated ({spec_name}) is not implemented. "
            f"Specs currently available are: ({' '.join(valid_specs.keys())})"
        )
    if len(l) == 2:
        spec_version = l[1]
        if (
            spec_version not in valid_specs[spec_name]["versions"]
            and spec_version != "latest"
        ):
            raise argparse.ArgumentTypeError(
                f"The spec {spec_name} is valid, but you indicated a version that is "
                f"not implemented: {spec_version}. Currently available options for this "
                f"spec are: {' '.join(valid_specs[spec_name]['versions'])}"
            )
    return x


def valid_file_type(x):
    if not os.path.isfile(x):
        raise argparse.ArgumentTypeError(
            f"The specified spec file path {x} does not lead to a valid / existing file."
            f"Please ensure you have correctly entered this!"
        )
    return x


def valid_folder_type(x):
    if not os.path.isdir(x):
        raise argparse.ArgumentTypeError(
            f"The specified spec path {x} does not lead to a valid / existing folder."
            f"Please ensure you have correctly entered this!"
        )
    return x


def add_sbatch_args(parser):
    """
    Helper function. Adds relevant arguments related to sbatch to the
    prep and prep-array command subparsers.
    :param parser: subcommand parser object
    :return: parser (enhanced with new arguments!)
    """
    parser.add_argument(
        "--time",
        "-t",
        type=valid_time,
        action="store",
        help="Manually specify wall time for running sbatch job. If you do, then you "
        "MUST specify hours, minutes, seconds in that order",
    )
    parser.add_argument(
        "--n-tasks",
        "--n_tasks",
        "-n",
        type=int,
        nargs=1,
        action="store",
        default=[8],
        help="Number of threads to request",
    )
    parser.add_argument(
        "--memory",
        "-m",
        type=int,
        nargs=1,
        action="store",
        default=[16000],
        help="Memory (in mb) to request",
    )
    parser.add_argument(
        "--sbatch-id",
        "--sbatch_id",
        "-s",
        type=int,
        nargs=1,
        help="Specify an sbatch job id, to identify the "
        "submission script to be created.",
        required=True,
    )
    parser.add_argument(
        "--no-header",
        "--no_header",
        action="store_true",
        help="Create sbatch job script, but without the sbatch header. Useful if you are "
        "creating this script as part of an array, or to run locally.",
    )
    return parser


def add_ids_args(parser, required=True):
    """
    Helper function. Adds arguments for ids to various subcommands.
    :param parser: subcommand parser object
    :return: parser (enhanced with new arguments!)
    """
    ids = parser.add_mutually_exclusive_group(required=required)
    ids.add_argument(
        "--ids",
        "-i",
        type=int,
        nargs="*",
        help="Specify specific job ids of interest",
        action="store",
    )
    ids.add_argument(
        "--range",
        "-r",
        type=int,
        nargs=2,
        help="Specify a range of job ids of interest. NB: this"
        "script INCLUDES the last id in the range.",
        action="store",
    )
    return parser


def add_logging_args(parser):
    """
    Helper function. Adds arguments for logging to parser object.
    :param parser: subcommand parser object
    :return: parser (enhanced with new arguments!)
    """
    # logging
    log_level = parser.add_mutually_exclusive_group(required=False)
    log_level.add_argument("--verbose", action="store_true")
    log_level.add_argument("--debug", action="store_true")

    return parser


def add_work_dir_path_args(parser):
    """
    Helper function. Adds arguments for pointing to work dir to parser object.
    :param parser: subcommand parser object
    :return: parser (enhanced with new arguments!)
    """

    # base folder
    base_folder = parser.add_mutually_exclusive_group(required=True)
    base_folder.add_argument(
        "--cluster",
        type=str,
        nargs=1,
        choices=["midway2-scratch"],
        action="store",
        help="Use defaults for a given HPC cluster to use. Currently, only "
        "UChicago Midway2 (run on user scratch) is implemented.",
    )
    base_folder.add_argument(
        "--wd-path",
        "--wd_path",
        type=valid_folder_type,
        nargs=1,
        action="store",
        help="Provide your own path to create a working directory tree. "
        "E.g., if you want this to be someplace like /project2/abcd/mystuff "
        "(less efficient...), or for testing",
    )

    parser.add_argument(
        "--userid",
        type=str,
        nargs=1,
        action="store",
        help="User ID (e.g., CNetID at UChicago) of the person using this. "
        "Required for some clusters (e.g., in midway2-scratch, to calculate the path "
        "to scratch where the pre-fabricated bash "
        "scripts are being stored. Ignored otherwise.",
    )

    return parser


def add_spec_args(parser):
    """
    Helper function. Adds arguments for specifying a spec to parser object.
    :param parser: subcommand parser object
    :return: parser (enhanced with new arguments!)
    """
    spec = parser.add_mutually_exclusive_group(required=True)
    spec.add_argument(
        "--spec-file",
        "--spec_file",
        type=valid_file_type,
        nargs=1,
        action="store",
        help="job specification yml file (if" "not implemented in main pkg)",
    )
    spec.add_argument(
        "--spec-builtin",
        "--spec_builtin",
        type=built_in_spec_type,
        nargs=1,
        action="store",
        help="job specification to load from built-ins. "
        "you may use <spec>:<version_tag> if you"
        "would like to use a specific version. if "
        "<spec> or <spec>:latest is provided, the latest version"
        "will be used.",
    )
    return parser


def add_dry_option(parser):
    """
    Helper function. Adds arguments for logging to parser object.
    :param parser: subcommand parser object
    :return: parser (enhanced with new arguments!)
    """
    # top-level parser arguments
    parser.add_argument(
        "--dry",
        action="store_true",
        required=False,
        help="Dry run - do not execute any scripts or run commands. "
        "Useful for debugging.",
    )
    return parser


def add_parser_options(parser, *args):
    """
    Helper function. Adds generic options (logging, dry, wd) to parser object.
    :param parser: subcommand parser object
    :return: parser (enhanced with new arguments!)
    """
    allowed = {"wd", "spec", "dry", "sbatch", "ids", "ids-optional"}
    opts = set(args)

    assert opts.issubset(allowed), "some of the args indicated are not yet implemented"
    # parser = copy.deepcopy(parser)

    if "wd" in opts:
        parser = add_work_dir_path_args(parser)

    if "sbatch" in opts:
        parser = add_sbatch_args(parser)

    if "ids" in opts:
        parser = add_ids_args(parser, required=True)

    if "ids-optional" in opts:
        parser = add_ids_args(parser, required=False)

    if "spec" in opts:
        parser = add_spec_args(parser)

    # by default, always add logging
    parser = add_logging_args(parser)

    if "dry" in opts:
        parser = add_dry_option(parser)

    return parser


def build_parser():
    """
    Utility function to build a parser object for this script.

    Credit where credit is due: I found this page immensely helpful in
    refactoring my code: https://www.iridescent.io/a-config-nightmare-argparse-a-deep-dive-part-2/

    :return: parser object :)
    """

    # create the top-level parser
    parser = argparse.ArgumentParser(
        prog="slurmhelper",
        description="A utility to make running sbatch job batches on "
        "your HPC a little easier! :)",
    )

    subparsers = parser.add_subparsers(
        title="commands", dest="operation", required=True
    )

    # create the parser for the "INIT" command
    # -----------------------------------------------------------------------
    init = subparsers.add_parser("init", help="initialize directory structure")
    init.add_argument(
        "--db",
        "-d",
        type=valid_file_type,
        nargs=1,
        action="store",
        help="database CSV file to use when initializing your working directory",
        required=True,
    )
    init.add_argument(
        "--full",
        action="store_true",
        help="in addition to init, also"
        "generate run/copy/clean scripts "
        "for all user jobs.",
    )
    init = add_parser_options(init, "wd", "spec", "dry")

    # create the parser for the "LIST" command
    # -----------------------------------------------------------------------
    list = subparsers.add_parser("list", help="print a list of existing scripts")
    list = add_parser_options(list, "wd")

    # create the parser for the "COPY" command
    # -----------------------------------------------------------------------
    copy = subparsers.add_parser("copy", help="copy inputs to working directory")
    copy = add_parser_options(copy, "wd", "spec", "dry", "ids")

    # create the parser for the "CLEAN" command
    # -----------------------------------------------------------------------
    clean = subparsers.add_parser(
        "clean", help="clean partial outputs & working " "dir data for a user job"
    )
    clean = add_parser_options(clean, "wd", "spec", "dry", "ids")

    # create the parser for the "PREP" command
    # -----------------------------------------------------------------------
    prep = subparsers.add_parser("prep", help="create wrapper for serial sbatch job")
    prep = add_parser_options(prep, "wd", "ids", "sbatch", "spec", "dry")

    # create the parser for the "PREP-ARRAY" command
    # -----------------------------------------------------------------------
    prep_array = subparsers.add_parser(
        "prep-array", help="create wrapper for sbatch job array"
    )
    prep_array = add_parser_options(prep_array, "wd", "ids", "sbatch", "spec", "dry")
    prep_array.add_argument(
        "--n-parcels",
        "-n_parcels",
        nargs=1,
        type=int,
        action="store",
        help="Manual override to specify number" "of parcels to divide yo jobz",
    )
    prep_array.add_argument(
        "--rate-limit",
        "--rate_limit",
        type=int,
        action="store",
        help="Limit the number of concurrent array jobs to"
        "the number provided, if specified.",
    )

    # create the parser for the "GENSCRIPTS" command
    # -----------------------------------------------------------------------
    genscripts = subparsers.add_parser("gen-scripts", help="generate user job scripts")
    genscripts = add_parser_options(genscripts, "wd", "spec", "ids-optional")

    # create the parser for the "CHECK" command
    # -----------------------------------------------------------------------
    check = subparsers.add_parser("check", help="run tests to validate jobs")
    check = add_parser_options(check, "wd", "spec", "ids")

    # create the parser for the "validate-spec" command
    # -----------------------------------------------------------------------
    validate_spec = subparsers.add_parser(
        "validate-spec", help="validate a user-given spec file"
    )

    return parser
