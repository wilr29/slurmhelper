Writing a specification
=======================

Specification files are written in YAML. Not all keys listed here are required - please refer to each item as you write your spec. I recommend using an existing template as a guide. You may check if a YAML file you have written is compliant with slurmhelper's spec format using the `slurmhelper validate-spec` command.

Minimal spec
------------
A minimal spec must include:

.. code-block::
    --
    spec_name = 'spec'
    spec_version = '2022-02-22'

    <TBD>


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
        * `output_base_dir` -- corresponds to your spec
        * `this_job_run_script`
        * `this_job_log_file`
        * `this_job_inputs_dir`
        * `this_job_work_dir`
        * `this_job_copy_script` -- available only if `copy_script` was provided
        * `this_job_clean_script` -- available only if `clean_script` was provided
        * `this_job_output_dir` -- available only if `output_path_subject` was provided. Note that this should be structured as a list, with each item being a level in the directory tree, and substitution keys formatted using a similar specification and referring to variables in your CSV database file.
        * `this_job_output_expr` -- available only if `this_job_output_dir` prerequisites and `output_path_subject_expr` were provided.
        * `this_job_output_expr_fullpath` -- available only if requirements for `this_job_output_expr` are met.

copy_script
    *Optional*. This can be used in case inputs need to be copied from another location, e.g., cold storage, prior to processing. Can also be used to move stuff to scratch for faster I/O. Please see the entry for `run_script` above for a list of all the available substitution variables for this template script.

clean_script
    *Optional*. This is a script that can be used to directly delete all the job-specific data from the working directory. This can be enormously helpful when re-running jobs! Please see the entry for `run_script` above for a list of all the available substitution variables for this template script.

Inputs and outputs
------------------

output_path
    *Required*. This is the base path for your outputs. Example: `/projects/mylab/studyBIDS/derivatives`

output_path_subject
    *Optional*. Useful for subject-specific paths, although I recommend maybe not using this and hardcoding in the script instead. expands the above to include subdirectories as given per each list item.

output_path_subject_expr
    *Optional*. TBD.

base_directory_name
    *Optional*. Name for the working directory structure to use with slurmhelper for your project. Defaults to `working`.

Job specification
-----------------

expected_n_files
    *Optional*. Expected number of output files to be derived. Can be used for a quick and dirty test of whether the run completed successfully.

job_ramp_up_time
    *Optional*. Ramp up time to build in to any serial job script. This might be relevant if, e.g., you are loading up MATLAB, doing some I/O task, etc.

job_time
    *Required*. Estimated time for a typical job. I recommend that you test some jobs, record times, and use the 90th percentile. You must indicate this in a subdictionary with keys `hours`, `minutes`, `seconds` (see example).

max_job_time
    *Required*. Maximum amount of time to spend in a serial job submission. This is the "wall time" to shoot for per serial sbatch job (or sbatch job array element). E.g., at UChicago, this is about 23 hours.

Custom submission variable computation (advanced)
-------------------------------------------------

compute_function
    *Optional*. Not yet implemented in a way that works... stay tuned! Hopefully, this would let you write your own function to compute additional fill-in variables in your run script from slurmhelper.