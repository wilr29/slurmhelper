import argparse

def build_parser():
    '''
    Utility function to build a parser object for this script
    :return: parser object :)
    '''

    # Validation for wall time manual specification...
    def wall_time_type(x):
        '''
        Definition of a wall time type for validating in argparse.
        :param x: list assumed to be of length 3 in order hours, minutes, seconds.
        :return: x (following validation)
        '''
        # Assertions
        assert (isinstance(x, list))
        assert (len(x) == 3)
        # Validation
        hours = x[ 0 ]
        minutes = x[ 1 ]
        seconds = x[ 2 ]
        if seconds > 59 or seconds < 0:
            raise argparse.ArgumentTypeError("Seconds value needs to be 0 <= secs < 60")
        elif minutes > 59 or minutes < 0:
            raise argparse.ArgumentTypeError("Minutes value needs to be 0 <= minutes < 60")
        elif hours > 23 or hours < 0:
            raise argparse.ArgumentTypeError("Hours value needs to be 0 <= hours < 24")

    parser = argparse.ArgumentParser(prog='runhelper', usage='%(prog)s operation [options]',
                                     description='Help with big slurm submission things')

    parser.add_argument('operation', type=str, choices=[ 'copy', 'clear', 'reset',
                                                         'prep', 'prep-array', 'list', 'check','init',
                                                         'genscripts'], action='store')
    spec = parser.add_mutually_exclusive_group()
    spec.add_argument('--spec', type=str, nargs=1, choices=['rshrfmatlab'], action='store',
                        help='job specification to load from built-ins.')
    spec.add_argument('--spec-file', '--spec_file', type=str, nargs=1, action='store', help='job specification yml file (if'
                                                                                   'not implemented in main pkg)')
    parser.add_argument('--cluster', type=str, default=['midway2-scratch'], choices=[ 'midway2-scratch', 'tmp'], action='store',
                        help='Name of the cluster preset to use. Currently, only UChicago Midway2 (run on user scratch)'
                             ' is implemented; tmp is offered as an option for debugging this pkg (to /tmp)')
    parser.add_argument('--cnet', type=str, default=[ 'fcmeyer' ], action='store',
                        help='CNetID of the person using this. Used to calculate the path to scratch where the'
                             'pre-fabricated bash scripts are being stored. Primarily here b/c UChicago.')
    parser.add_argument('--dry', '-d', action='store_true',
                        help='Dry run - do not execute any scripts or run commands. Useful for debugging.')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--ids', '-i', type=int, nargs='*', help='Specify specific job ids of interest', action='store')
    group.add_argument('--range', '-r', type=int, nargs=2, help='Specify a range of job ids of interest. NB: this'
                                                                'script INCLUDES the last id in the range.',
                       action='store')

    sbatch = parser.add_argument_group(title='sbatch', description='Options for the sbatch submissions script')

    sbatch.add_argument('--time', '-t', type=wall_time_type, nargs=3, action='store',
                        help='Manually specify wall time for running sbatch job. If you do, then you '
                             'MUST specify hours, minutes, seconds in that order')
    sbatch.add_argument('--n_tasks', '-n', type=int, nargs=1, action='store', default=[ 8 ],
                        help='Number of threads to request')
    sbatch.add_argument('--memory', '-m', type=int, nargs=1, action='store', default=[ 16000 ],
                        help='Memory (in mb) to request')
    sbatch.add_argument('--sbatch_id', '-s', type=int, nargs=1, help='Specify an sbatch job id, to identify the '
                                                                     'submission script to be created.')
    sbatch.add_argument('--no_header', '-x', action='store_true',
                        help='Create sbatch job script, but without the sbatch header. Useful if you are '
                             'creating this script as part of an array, or to run locally.')

    sarray = parser.add_argument_group(title='sarray', description='Options pertaining to creating an array of jobs')
    # sarray.add_argument('--array_id', type=int, nargs=1, action='store',help = 'Identifier for the sbatch array you'
    #                                                                            'are planning to submit.' )
    sarray.add_argument('--n_parcels', '-p', nargs=1, type=int,action='store',help='Manually override, specify number'
                                                                                   'of parcels to divide yo jobz')
    sarray.add_argument('--rate_limit', type=int, action='store', help='Limit the number of concurrent array jobs to'
                                                                       'the number provided, if specified.')

    parser.add_argument('--verbose', '-v', action='store_true')

    return parser