def compute_custom_vars(job_dict, dirs):
    """
    DO NOT CHANGE THE NAME OR ARGS OF THIS FUNCTION!!!!!!

    This function will receive as input a dictionary representing all
    the run parameters for a given job, enhanced with all the keys
    provided as global run parameters in your specification YAML file.

    It will also receive as input a dictionary referencing various
    helpful paths in your structure, for example:

    {'base': '/home/fcmeyer/scratch-midway2/running',
     'checks': '/home/fcmeyer/scratch-midway2/running/checks',
     'slurm_scripts': '/home/fcmeyer/scratch-midway2/running/scripts/slurm',
     'slurm_logs': '/home/fcmeyer/scratch-midway2/running/logs/slurm',
     'job_scripts': '/home/fcmeyer/scratch-midway2/running/scripts/jobs',
     'job_logs': '/home/fcmeyer/scratch-midway2/running/logs/jobs',
     'job_inputs': '/home/fcmeyer/scratch-midway2/running/inputs',
     'job_work': '/home/fcmeyer/scratch-midway2/running/work'}

    If you are planning to have some job-specific stuff be computed,
    then please ensure that the return of this function is a dict
    including all the key:items in job_dict, plus the key:item pairs
    you would like to estimate for a job.

    NOTE: the parameters 'job_id', 'path_work' and 'path_inputs'
          were already automatically calculated for you and added
          to the dict you are getting. Please do NOT estimate them here!
          If they are not needed for your spec, they will be cleared out :)

    TIP: please include any non-base python imports within the scope of this
         function (under the def: statement) since they might not be loaded in my
         og code. Also, make sure you install them to your env!

    :param job_dict: a dictionary representing a row. for example, if
    you had a csv file with rows [sub,ses,task,run,order_id], and also
    defined globals [conda_env_path, matlab_path], you would get a dict
    {
        sub: NIDA2322 ses: 1, task: 'rest', run: 2, order_id:5,
        conda_env_path:'/project2/conda/myenv', matlab_path:'/usr/bin/matlab'
    }
    :param dirs: output of ..utils.io:calculate_directories()
    :return: job_dict, plus keys you add!
    """
    from pathlib import Path

    job_dict["run_inputs"] = str(
        Path(dirs["job_work"])
        .joinpath("%05d" % job_dict["order_id"])
        .joinpath("derivatives")
    )

    # If you do not have anything to add, just return job_dict.
    return job_dict
