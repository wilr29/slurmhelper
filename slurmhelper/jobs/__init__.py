"""This python submodule contains helper classes and functions for dealing with jobs.
In this package, a "job" is defined as a single submissible script, which can be part of
a broader "package" or array of jobs, or not. For the purposes of this package, here I
consider a specific "job" calculation of a given neuroimaging derivative, for a given neuroimaging run,
of a given task, of a given session, of a given subject. Others may choose to parcellate "jobs" more or
less grossly.
"""

from .scriptwriter import generate_run_scripts
from .job import Job, TestableJob
from ..utils.io import write_job_script
from ..utils.misc import split_list
from ..utils.time import calculate_wall_time, calculate_min_number_of_parcels
import os
from string import Template

# Implementation of the prep portion of the script...
def prep_job(config, job_list, paths, args, array_job_index=None):
    '''
    Will create a submission wrapper for one or more jobs, which
    are aggregated to be run serially. This function can be used for
    preparing a (non-array) sbatch wrapper for a job, or a serial-
    run script that is then "arrayified" by prep_job_array().

    :param config: dict, output of load_spec()
    :param job_list: list of jobs to prepare
    :param paths: dict output of calculate_directories()
    :param args: parsed ArgParse object
    :param array_job_index: None if this is not to be run as array;
                            integer if part of array.jobs
❯ ls
00001_clean.sh 00001_run.sh   00002_copy.sh  00003_clean.sh 00003_run.sh
00001_copy.sh  00002_clean.sh 00002_run.sh   00003_copy.sh
(base)
slurmhelper_testing/scripts/jobs
❯ cat
    :return: job_name: name of script to run job
    '''

    print("========== BEGIN DOING STUFF ==========")
    # Wall time
    if args.time is not None:  # use manually specified time
        time = "{hours:02d}:{minutes:02d}:{seconds:02d)".format(hours=args.time[ 0 ], minutes=args.time[ 1 ],
                                                                seconds=args.time[ 2 ])
    else:  # calculate wall time using our current assumptions
        time = calculate_wall_time(len(job_list),config)

    # Give me a good job name
    if args.operation == 'prep-array' and array_job_index is not None:
        job_name = 'sb-{sbatch_id:04d}-{array_job_index:03d}'.format(sbatch_id=args.sbatch_id[ 0 ],
                                                                     array_job_index=array_job_index)
    else:
        job_name = 'sb-{sbatch_id:04d}'.format(sbatch_id=args.sbatch_id[ 0 ])

    # begin assembling the thingy
    if args.no_header or args.operation == 'prep-array':
        header_f = '\n'.join([ '''#!/bin/bash -e''', config['preamble']])
    else:
        # Figure out the log path
        log_out = os.path.join(paths['slurm_logs'], '{job_name}.txt'.format(job_name=job_name))
        header_f = '\n'.join([ Template(config['header']).safe_substitute(job_name=job_name, log_path=log_out, n_tasks=args.n_tasks[ 0 ],
                                             mem=args.memory[ 0 ], time=time, job_array=''), config['preamble'] ])

    # Ok, let's create the section where we call each job script.
    script_call = 'bash {target_path} 2>&1 | tee {job_log_path}'

    job_calls = [ ]
    for job_id in job_list:
        script_name = '{job_id:05d}_run.sh'.format(job_id=job_id)
        target_path = os.path.join(paths['job_scripts'], script_name)
        job_log_path = os.path.join(paths['job_logs'], '{job_id:05d}.txt'.format(job_id=job_id))
        job_calls.append(script_call.format(target_path=target_path, job_log_path=job_log_path))

    job_calls_str = '\n'.join(job_calls)
    script = '\n\n'.join([ header_f, job_calls_str, '''echo "~~~~~~~~~~~~~ END SLURM JOB ~~~~~~~~~~~~~~"''', 'exit' ])

    if not args.dry:
        write_job_script(job_name, args.sbatch_id[0], paths, script)

    if args.verbose or args.dry:
        print("script will be written to: {path}".format(
            path=os.path.join(paths[ 'slurm_scripts' ], '{name}.sh'.format(name=job_name))))
        print("Contents of written script:\n------------------\n")
        print(script)

    print("========== TOTALLY DONE! YEE HAW :) ==========")

    return job_name

# this does the array stuff
def prep_job_array(config, job_list, paths, args):
    '''
    Will create an array-ified submission wrapper a list of jobs, which
    are automagically arranged into an optimized array of serial jobs :)

    :param config: dict, output of load_spec()
    :param job_list: list of jobs to prepare
    :param paths: dict output of calculate_directories()
    :param args: parsed ArgParse object
    :return: job_name: name of script to run job
    '''
    # allow for manual override of number of parcels, else, calculate it
    if args.n_parcels is not None:
        n_parcels = args.n_parcels[ 0 ]
    else:
        n_parcels = calculate_min_number_of_parcels(len(job_list))

    # divvy up my jobs evenly
    job_array = split_list(job_list, wanted_parts=n_parcels)

    # verbose print statement because, reasons
    if args.verbose:
        print("JOB ARRAY IS:")
        print(job_array)

    # for each parcel to include in the array
    for i in range(0, n_parcels):
        # retrieve my parcel
        parcel = job_array[ i ]
        arr_j_i = i + 100
        # make as many jobs as we want, each job is a buddy :)
        # this will write out the sub_job scripts too
        prep_job(config, parcel, paths, args, array_job_index=arr_j_i)

    # ok, here's the array script...
    job_name = 'sb-{sbatch_id:04d}'.format(sbatch_id=args.sbatch_id[ 0 ])  # notice, we still have an sb- name, this is

    # for all jobs submitted...
    # Wall time
    if args.time is not None:  # use manually specified time
        time = "{hours:02d}:{minutes:02d}:{seconds:02d)".format(hours=args.time[ 0 ], minutes=args.time[ 1 ],
                                                                seconds=args.time[ 2 ])
    else:  # calculate wall time using our current assumptions
        parcel_lengths = [ len(p) for p in job_array ]
        time = calculate_wall_time(max(parcel_lengths), config)  # we should use the maximum wall time for parcels

    # Figure out the log path
    log_out = os.path.join(paths['slurm_logs'],'{job_name}-%a.txt'.format(job_name=job_name))
    if args.rate_limit is not None:
        steppity = '''%{rate}'''.format(rate=args.rate_limit)
    else:
        steppity = ''

    arr = '#SBATCH --array={start_index:d}-{end_index:d}{step}'.format(start_index=100, end_index=(100 + n_parcels - 1),
                                                                       step=steppity)
    path_to_array = os.path.join(paths['slurm_scripts'],
                                 'sb-{sbatch_id:04d}-$SLURM_ARRAY_TASK_ID.sh'.format(sbatch_id=args.sbatch_id[ 0 ]))

    array_script = '\n'.join([ config['header'].format(job_name=job_name, log_path=log_out, n_tasks=args.n_tasks[ 0 ],
                                             mem=args.memory[ 0 ], time=time, job_array=arr),
                               Template(config['array_footer']).safe_substitute(path_to_array=path_to_array) ])
    if not args.dry:
        # finally, write out the array script
        write_job_script(job_name, args.sbatch_id[0], paths, array_script)

    if args.verbose or args.dry:
        print("script will be written to: {path}".format(path=os.path.join(paths['slurm_scripts']
                                                                                 ,'{name}.sh'.format(name=job_name))))
        print("Contents of ARRAY script:\n------------------\n")
        print(array_script)

    return