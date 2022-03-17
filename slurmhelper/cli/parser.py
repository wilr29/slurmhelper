import argparse
from slurmhelper.utils.time import wall_time_type

def add_sbatch_args(parser):
    '''
    Helper function. Adds relevant arguments related to sbatch to the
    prep and prep-array command subparsers.
    :param parser: subcommand parser object
    :return: parser (enhanced with new arguments!)
    '''
    parser.add_argument('--time', '-t', type=wall_time_type, nargs=3, action='store',
                        help='Manually specify wall time for running sbatch job. If you do, then you '
                             'MUST specify hours, minutes, seconds in that order')
    parser.add_argument('--n-tasks', '--n_tasks', '-n', type=int, nargs=1, action='store', default=[8],
                        help='Number of threads to request')
    parser.add_argument('--memory', '-m', type=int, nargs=1, action='store', default=[16000],
                        help='Memory (in mb) to request')
    parser.add_argument('--sbatch-id', '--sbatch_id','-s', type=int,
                        nargs=1, help='Specify an sbatch job id, to identify the '
                                       'submission script to be created.')
    parser.add_argument('--no-header', '--no_header', action='store_true',
                        help='Create sbatch job script, but without the sbatch header. Useful if you are '
                             'creating this script as part of an array, or to run locally.')
    return parser

def add_ids_args(parser, required=True):
    '''
    Helper function. Adds arguments for ids to various subcommands.
    :param parser: subcommand parser object
    :return: parser (enhanced with new arguments!)
    '''
    ids = parser.add_mutually_exclusive_group(required=required)
    ids.add_argument('--ids', '-i', type=int, nargs='*',
                     help='Specify specific job ids of interest', action='store')
    ids.add_argument('--range', '-r', type=int, nargs=2,
                     help='Specify a range of job ids of interest. NB: this'
                           'script INCLUDES the last id in the range.',
                     action='store')
    return parser


def build_parser():
    '''
    Utility function to build a parser object for this script.

    Credit where credit is due: I found this page immensely helpful in
    refactoring my code: https://www.iridescent.io/a-config-nightmare-argparse-a-deep-dive-part-2/

    :return: parser object :)
    '''

    # create the top-level parser
    parser = argparse.ArgumentParser(prog='slurmhelper',
                                     description='A utility to make running sbatch job batches on '
                                                 'your HPC a little easier! :)')
    # top-level parser arguments
    parser.add_argument('--verbose', '-v', action='store_true')
    parser.add_argument('--dry', '-d', action='store_true',
                        help='Dry run - do not execute any scripts or run commands. '
                             'Useful for debugging.')
    parser.add_argument('--cluster', type=str, default=['midway2-scratch'],
                        choices=[ 'midway2-scratch', 'tmp'], action='store',
                        help='Name of the cluster preset to use. Currently, only '
                             'UChicago Midway2 (run on user scratch) is implemented; '
                             'tmp is offered as an option for debugging this pkg (to /tmp)')
    parser.add_argument('--cnet', type=str, default=['fcmeyer'], action='store',
                        help='CNetID of the person using this. Used to calculate the path '
                             'to scratch where the pre-fabricated bash scripts are being stored. '
                             'Primarily here b/c UChicago. Ignored otherwise.')

    spec = parser.add_mutually_exclusive_group(required=True)
    spec.add_argument('--spec-name','--spec_name', type=str, nargs=1,
                      choices=['rshrfmatlab'], action='store',
                      help='job specification to load from built-ins.')
    spec.add_argument('--spec-file', '--spec_file', type=str, nargs=1, action='store',
                      help='job specification yml file (if'
                           'not implemented in main pkg)')

    # TODO: additional validation here.
    spec.add_argument('--spec-version','--spec_version',type=str, nargs=1,
                      action='store', help='version of the spec to use. only considered'
                                           'if spec-name is provided.')

    subparsers = parser.add_subparsers(help='sub-command help')

    # create the parser for the "INIT" command
    # -----------------------------------------------------------------------
    init = subparsers.add_parser('init', help='initialize directory structure')
    init.add_argument('number', type=int, help='number help')

    # create the parser for the "LIST" command
    # -----------------------------------------------------------------------
    list = subparsers.add_parser('list', help='print a list of existing scripts')

    # create the parser for the "COPY" command
    # -----------------------------------------------------------------------
    copy = subparsers.add_parser('copy', help='copy inputs to working directory')
    copy = add_ids_args(copy)

    # create the parser for the "CLEAN" command
    # -----------------------------------------------------------------------
    clean = subparsers.add_parser('clean', help='clean partial outputs & working '
                                                'dir data for a user job')
    clean = add_ids_args(clean)

    # create the parser for the "PREP" command
    # -----------------------------------------------------------------------
    prep = subparsers.add_parser('prep', help='create wrapper for serial sbatch job')
    prep = add_ids_args(prep)
    prep = add_sbatch_args(prep)

    # create the parser for the "PREP-ARRAY" command
    # -----------------------------------------------------------------------
    prep_array = subparsers.add_parser('prep-array', help='create wrapper for sbatch job array')
    prep_array = add_ids_args(prep_array)
    prep_array = add_sbatch_args(prep_array)
    prep_array.add_argument('--n-parcels', '-n_parcels', nargs=1,
                            type=int, action='store', help='Manual override to specify number'
                                                           'of parcels to divide yo jobz')
    prep_array.add_argument('--rate-limit', '--rate_limit', type=int, action='store',
                            help='Limit the number of concurrent array jobs to'
                                 'the number provided, if specified.')

    # create the parser for the "GENSCRIPTS" command
    # -----------------------------------------------------------------------
    genscripts = subparsers.add_parser('genscripts', help='generate user job scripts')
    genscripts = add_ids_args(genscripts, required=False)

    # create the parser for the "CHECK" command
    # -----------------------------------------------------------------------
    check = subparsers.add_parser('check', help='run tests to validate jobs')
    check = add_ids_args(check)

    return parser
