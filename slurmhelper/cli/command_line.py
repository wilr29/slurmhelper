import numpy as np
import os
from .parser import build_parser
from ..utils.io import calculate_directories, calculate_directories_midwayscratch, \
    copy_or_clean, initialize_directories
from ..utils.reporting import list_slurm, check_runs
from ..jobs import prep_job, prep_job_array, generate_run_scripts
from ..config import load_rshrfmatlab_spec, load_job_spec

def main():
    '''
    Command-line entrypoint. Constructs and parses CLI inputs, and runs specified function.
    :return: None
    '''
    # Build parser, and parse arguments
    parser = build_parser()
    args = parser.parse_args()

    if args.verbose:
        print("ARGUMENTS SPECIFIED:")
        print(args)

    # Spit out errors if needed.
    if (args.operation == 'prep' or args.operation == 'prep-array') and not args.sbatch_id:
        parser.error('You must specify an sbatch job identifier if you want to prep a sbatch submission, '
                     'whether it is array or standalone.')
    elif (args.operation != 'prep' and args.operation != 'prep-array') and args.sbatch_id is not None:
        parser.error('You should NOT be specifying an sbatch id if you do not intend to prep a job.')
    elif (args.operation not in {'list', 'init','genscripts'} and args.ids is None and args.range is None):
        parser.error('You must specify either a list of IDs or a range of IDs for this operation.')

    # Compile subject list, if required
    if not ((args.operation in {'list', 'init'}) or (args.operation == 'genscripts' and args.ids is None
                                                     and args.range is None)):
        # needed for everything except list, and init
        job_list = []
        if args.ids is not None:
            job_list += args.ids
        else:
            job_list += np.arange(args.range[0], args.range[1] + 1).tolist()

    # Print some messages for friendliness :)
    print("Runhelper will run the {op} operation.".format(op=args.operation))
    if not ((args.operation in {'list', 'init'}) or (args.operation == 'genscripts' and args.ids is None
                                                     and args.range is None)):
        print("A total of {n} jobs will be affected by this call.".format(n=len(job_list)))

    # Verbose only
    if args.verbose and not ((args.operation in {'list', 'init'}) or
                             (args.operation == 'genscripts' and args.ids is None and args.range is None)):
        print("\nThese jobs are:")
        print(job_list)

    # load config
    if args.spec is not None:
        if args.spec[0] == 'rshrfmatlab':
            version='latest'
            if args.spec_version is not None:
                version=args.spec_version[0]
            config = load_rshrfmatlab_spec(version)
        else:
            raise ValueError("Invalid spec provided?")
    elif args.spec_file is not None:
        assert os.path.exists(args.spec_file[0]), "File %s does not exist!" % (args.spec_file[0])
        config = load_job_spec(args.spec_file[0])

    if args.verbose:
        print("Loaded job specification with keys:\n%s" % (' '.join(config.keys())))

    if 'base_directory_name' not in config.keys():
        base_dir_name = 'working'
        print("Base dir name not specified; using default ('working')")
    else:
        base_dir_name = config['base_directory_name']

    # TODO: implement more clusters / ability for user to insert own config here

    if args.cluster == 'midway2-scratch':
        paths = calculate_directories_midwayscratch(args.cnet[0], base_dir_name)
    elif args.cluster == 'tmp': # for debugging
        paths = calculate_directories('/tmp/slurmhelper_testing', base_dir_name)
    else:
        raise ValueError("The cluster indicated (%s) is not yet implemented..." % args.cluster)

    # More verbose (this is a chatty program)
    if args.verbose:
        print("\nExpect to find bash helper scripts in directory:")
        print(paths['job_scripts'])

    if args.operation == 'init':
        initialize_directories(paths)
    elif args.operation == 'genscripts':
        if args.ids is None and args.range is None:
            generate_run_scripts(paths, config, args)
        else:
            generate_run_scripts(paths, config, args, job_list)
    elif args.operation == 'copy' or args.operation == 'clean':
        copy_or_clean(job_list, args.operation, paths['job_scripts'])
    elif args.operation == 'reset':
        print("Will clear first, copy next!")
        try:
            copy_or_clean(job_list, 'clean', paths['job_scripts'])
            copy_or_clean(job_list, 'copy', paths['job_scripts'])
        except Exception as e:
            raise e
    elif args.operation == 'prep':
        prep_job(config, job_list, paths, args)
    elif args.operation == 'list':
        list_slurm(paths)
    elif args.operation == 'prep-array':
        prep_job_array(config, job_list, paths, args)
    elif args.operation == 'check':
        check_runs(job_list, paths, args, config)