'''
Various functions to optimize sbatch arrays given time constraints & prior
knowledge of what to expect
'''

import math

def delta_to_slurm_time(tdelta):
    '''
    Format a timedelta object into sbatch-compatible notation
    :param tdelta: timedelta object
    :return: formatted string for use in a script
    '''
    d = {"days": tdelta.days}
    d["hours"], rem = divmod(tdelta.seconds, 3600)
    d["minutes"], d["seconds"] = divmod(rem, 60)
    if tdelta.days == 0:
        as_string = '{hours}:{minutes}:{seconds}'.format(**d)
    else:
        as_string = '{days}-{hours}:{minutes}:{seconds}'.format(**d)
    return as_string

def calculate_wall_time(n_jobs, config):
    '''
    Function to calculate the total time for a long job script. This will operate from certain assumptions about
    time to "ramp up" and load modules, etc., and time consumed per job.
    :param n_jobs: number of jobs in script being prepped
    :return: wall time, formatted as string
    '''

    wall_time = config['job_ramp_up_time'] + n_jobs * config['job_time']
    return delta_to_slurm_time(wall_time)

def calculate_min_number_of_parcels(n_jobs, config):
    '''
    Estimate the minimum number of parcels necessary such that the time per parcel would not
    exceed the maximum time per job recommended by the team
    :param n_jobs: number of total jobs to be submitted by you greedy user
    :return: minimum number of array parcels to divide things into
    '''
    # assumption: divide ids in equal numbers of packets, such that no list is longer than 23 hours
    max_job_time_secs = config['max_job_time'].total_seconds()
    total_time = n_jobs * config['job_time'].total_seconds()
    return math.ceil(total_time / max_job_time_secs)