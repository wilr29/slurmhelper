Writing a specification
=======================

Specification files are written in YAML.

Spec information
----------------

spec_name
    Name of the specification

spec_version
    Version code for the specification, if applicable (e.g., if adapted for new pipeline)

Submission scripts
------------------

Global run parameters
^^^^^^^^^^^^^^^^^^^^^

script_global_settings
    dictionary with script substitution parameters that should be consistent across jobs.
    We propose directly stating this in the job spec for reproducibility and clarity.
    This could include, for example: number of threads, memory allocation, path to a conda environment
    / MATLAB / some other executable or dependency...

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

sbatch submission script template chunks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

header
    This should include a call to the shell you are using, and a ``#SBATCH`` header template.

preamble
    This should include any calls to load modules, activate conda environments, etc. Basically, anything you
    need to do to ensure your environment is adequately set up PRIOR to running a given job / call to your program.

array_footer
    Additional code to append at the end of the sbatch submission script. You may, for example, print timing information
    if you are examining a pipeline's performance; or you may print job information for subsequent examination of
    sbatch logs.

Job scripts
^^^^^^^^^^^

run_script
    Each job must have a "run" script, which includes the **basic call** to run the given process. E.g., if I am doing
    fMRI preprocessing, this would be a call to FMRIPREP. You may customize the job script as you wish to print more
    helpful outputs, and include custom parameters.

copy_script
    This can be used in case inputs need to be copied from another location, e.g., cold storage, prior to processing.
    Can also be used to move stuff to scratch for faster I/O.

clean_script
    This is a script that can be used to directly delete all the job-specific data from the working directory. This
    can be enormously helpful when re-running jobs!

Inputs and outputs
------------------

database
    TBD

output_path
    TBD

output_path_subject
    TBD

output_path_subject_expr
    TBD

base_directory_name
    TBD

Job specification
-----------------

expected_n_files
    TBD

job_ramp_up_time
    TBD

job_time
    TBD

max_job_time
    TBD

Custom submission variable computation (advanced)
-------------------------------------------------

compute_function
    TBD