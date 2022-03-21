Writing a specification
=======================

Specification files are written in YAML. Not all keys listed here are required - please refer to each item as you write your spec. I recommend using an existing template as a guide. You may check if a YAML file you have written is compliant with slurmhelper's spec format using the `slurmhelper validate-spec` command.

Spec definition
--------------

spec_name
    *Required.* Name of the specification.

spec_version
    *Required*. Version code for the specification. It is suggested that you specify
    this in ISO-compliant date format (e.g., 2022-03-22).


Submission scripts
------------------

sbatch submission script template chunks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

header
    *Required*. A formattable header to include in any sbatch submission script.
    This should include a call to the shell you are using, and a ``#SBATCH`` header template.
    For smart substitution, please include fields denoted as `${variablename}`. Allowed variables for substitution include the following:

        * `job_name`: filled in automatically as `sb-<sbatch_id>`.
        * `log_path`: filled in automatically as `<your_working_directory>/logs/sbatch/sb-<sbatch_id>.txt`
        * `n_tasks`: filled in from the `--n_tasks` argument provided to the `slurmhelper prep` or `slurmhelper prep-array` call.
        * `mem`: from the `--memory` argument provided to the `slurmhelper prep` or `slurmhelper prep-array` CLI call.
        * `time`: estimated based on the time-per-job parameters indicated in your spec, or manually provided in your `slurmhelper prep` or `slurmhelper prep-array` CLI call.

    Example:

    .. code-block::
        header : |
            #!/bin/bash -e

            #SBATCH --job-name=${job_name}
            #SBATCH --output=${log_path}
            #SBATCH --partition=broadwl
            #SBATCH --nodes=1
            #SBATCH --ntasks-per-node=${n_tasks}
            #SBATCH --mem=${mem}
            #SBATCH --time=${time}
            ${job_array}

preamble
    *Optional.* This could include any calls to load modules, activate conda environments,
    etc. Basically, anything you need to do to ensure your environment is adequately set up
    PRIOR to running a given job / call to your program.

    ..note:: This is meant to be a fixed template; no variable substitution will be provided here.

array_footer
    *Optional.* Additional code to append at the end of the sbatch submission script. You may, for example, print timing information if you are examining a pipeline's performance; or you may print job information for subsequent examination of sbatch logs.

    ..note:: This is meant to be a fixed template; no variable substitution will be provided here.

Global run parameters
^^^^^^^^^^^^^^^^^^^^^

script_global_settings
    *Optional*. A dictionary with script substitution parameters that should be consistent across jobs. I propose directly stating this in the job spec for reproducibility and clarity. This could include, for example: number of threads, memory allocation, path to a conda environment / MATLAB / some other executable or dependency.

    In my rshrfmatlab spec, I use the following:

    .. code-block::

        script_global_settings : {
                          n_thr: 1,
                          mem_mb: 1,
                          fd_thr: 0.3,
                          path_matlab: '/matlab',
                          path_spm: '/spm',
                          path_outputs: '/outputs'
        }

Job scripts
^^^^^^^^^^^

run_script
    *Required.* Template script to run jobs for this spec. This template must include the **basic call** to run the given process, as well as any post-run tasks that are to be completed by the compute node (e.g., removing temporary files, printing outcome, etc.). For example, if I am doing fMRI preprocessing, this would be a call to FMRIPREP. You may customize the job script as you wish to print more helpful outputs, and include custom parameters.

    For this script, you may count on the following substitution variables:

    1. If a `script_global_settings` dictionary is defined in your spec, then any variables that are provided there will be available for substitution in any job template script. E.g., for the example defined above, `n_thr`, `mem_mb`, `fd_thr`, `path_matlab`, `path_spm`, and `path_outputs` would be made available.
    2. Any variables in your input CSV database file, including `order_id`.
    3. The following job-specific paths:

        .. code-block::

            TBD

copy_script
    *Optional*. This can be used in case inputs need to be copied from another location, e.g., cold storage, prior to processing. Can also be used to move stuff to scratch for faster I/O. Please see the entry for `run_script` above for a list of all the available substitution variables for this template script.

clean_script
    *Optional*. This is a script that can be used to directly delete all the job-specific data from the working directory. This can be enormously helpful when re-running jobs! Please see the entry for `run_script` above for a list of all the available substitution variables for this template script.

Inputs and outputs
------------------

database
    *Required*. This is a...

output_path
    *Required*. This is...

output_path_subject
    *Optional*. This is...

output_path_subject_expr
    *Optional*. This is...

base_directory_name
    *Optional*. This is....

Job specification
-----------------

expected_n_files
    *Optional*. This is...

job_ramp_up_time
    *Optional*. This is...

job_time
    *Required*. This is...

max_job_time
    *Required*. This is...

Custom submission variable computation (advanced)
-------------------------------------------------

compute_function
    *Optional*. This is...