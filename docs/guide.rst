How it works
============

This project requires you to understand the following concepts:

1. **User Job**: A user job is defined as a command that can be run by slurm from based on the specification provided, and the
   job-specific parameters from a given row in a CSV file that you provide. There is flexibility on what exactly can
   constitute a "job"; in my case, I consider a "job" as a pipeline that receives as input data from one run,
   of one task, for one session, for one subject. Others may define this differently, depending on the use case.

2. **Sbatch Job**: A slurm job consists of one (or more, if aggregated serially) user job(s) wrapped in an sbatch
   submission script, for computation in an HPC that uses SLURM.

3. **Sbatch Job Array**: A slurm job array consists of two or more slurm jobs with identical sbatch parameters (e.g.,
   memory allocation, cpus allocation, time allocation) that are submitted to SLURM together.

When one has many user jobs, there is flexibility in how this is organized.

Simple scenario: three user jobs, one sbatch job, no arrays
-----------------------------------------------------------

For a single user job (no array), this script will generate the following:

Job run script
    This is located in ``<wd>/scripts/jobs/<job_id>_run.sh``. This is a base code call for a job. This job run script
    assumes all environment variables and dependencies are already loaded, so one can focus on the specific call. This
    will be generated procedurally based on your database and global parameters. See below for an example of a job
    run script::

        #!/bin/bash -e

        echo "Begin running job 00001, corresponding to:"
        echo "Subject NDARINVFBE9UXHG, Session baselineYear1Arm1, Task rest, Run 2"
        echo "-----------------------------"

        rshrfmatlab --nthreads 8 --mem_mb 15000 --trim_amt 8 --trim_tgt 375 \
            --participant_label NDARINVFBE9UXHG --session_label baselineYear1Arm1 \
            --task-id rest --run-id 2 --fd_thr 0.300 --tr 0.800 --serial-corr 'AR(1)' \
            --basis_functions sfir canontdd \
            --keep_deconv roi \
            --atlas-parametermaps craddock400 shen268 \
            --atlas-deconv craddock400 shen268 \
            --keep_non_olrm \
            /software/matlab-2020b-el7-x86_64/bin/matlab \
            /home/fcmeyer/scratch-midway2/spm12 \
            /home/fcmeyer/scratch-midway2/running/inputs/00001/derivatives \
            /project2/abcd/derivatives \
            /home/fcmeyer/scratch-midway2/running/work/00001

        exit_status=$?

        echo "exit status: $exit_status"

        if [ $exit_status -eq 0 ]
        then
            echo "it appears things went well, go ahead and rm work and input dirs from scratch"
            rm -rf /home/fcmeyer/scratch-midway2/running/work/00001
            rm -rf /home/fcmeyer/scratch-midway2/running/inputs/00001
            echo "SUCCESS"
            echo $exit_status
            exit 0
        else
            echo "it appears things did not go well. we won't touch nothing"
            echo "FAILURE"
            echo $exit_status
            exit 1
        fi

Sbatch submission script
    This is located in ``<wd>/scripts/sbatch/sb-<sbatch_id>.sh``. This is a "wrapper" that is
    submitted to sbatch. This could look something like::

        #!/bin/bash -e

        #SBATCH --job-name=sb-0001
        #SBATCH --output=/home/fcmeyer/scratch-midway2/running/logs/slurm/sb-0001.txt
        #SBATCH --partition=broadwl
        #SBATCH --nodes=1
        #SBATCH --ntasks-per-node=8
        #SBATCH --mem=16000
        #SBATCH --time=2:20:0

        # load necessary modules
        module load python
        module load matlab/2020b
        module load fsl/6.0.4
        module load afni/21.0

        source activate /home/fcmeyer/scratch-midway2/rshrfmatlab

        echo "~~~~~~~~~~~~~ BEGIN SLURM JOB ~~~~~~~~~~~~~~"

        bash /home/fcmeyer/scratch-midway2/running/scripts/jobs/00001_run.sh 2>&1 | tee /home/fcmeyer/scratch-midway2/running/logs/jobs/00001.txt
        bash /home/fcmeyer/scratch-midway2/running/scripts/jobs/00002_run.sh 2>&1 | tee /home/fcmeyer/scratch-midway2/running/logs/jobs/00002.txt
        bash /home/fcmeyer/scratch-midway2/running/scripts/jobs/00003_run.sh 2>&1 | tee /home/fcmeyer/scratch-midway2/running/logs/jobs/00003.txt

        echo "~~~~~~~~~~~~~ END SLURM JOB ~~~~~~~~~~~~~~"


As this example illustrates, ``sb-0001.sh`` (the sbatch submission script) loads required modules and calls each of the
job scripts serially (``0000?_run.sh``). Each job's output logs are stored to a separate file for subsequent inspection,
and the overall logs for the sbatch wrappper are also stored in a file matching the ``sbatch_id`` indicated.

More complex scenario: job arrays
---------------------------------

TBD
