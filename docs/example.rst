Example
=======

Using rshrf matlab spec, I have the following csv file in my home directory (recall
this is where the spec expects it to be)::

    ❯ cat ~/rshrf_db.csv
    subject,session,task,run,tr,trim_amt,trim_tgt,order_id
    NDARINVFBE9UXHG,baselineYear1Arm1,rest,2,0.8,8,375,1
    NDARINVHNER3YDN,baselineYear1Arm1,rest,1,0.8,5,375,2
    NDARINVHNER3YDN,baselineYear1Arm1,rest,2,0.8,5,375,3

Initializing working directory
------------------------------

I initialize the working dir using the following command::

    slurmhelper init --cluster tmp --spec rshrfmatlab

This yields::

    .
    └── running
        ├── checks
        ├── inputs
        ├── logs
        │   ├── jobs
        │   └── slurm
        ├── scripts
        │   ├── jobs
        │   └── slurm
        └── work

    10 directories, 0 files

Creating user job scripts
-------------------------

Ok, so now I create the copy, clear and run user job scripts for all user jobs
in the list as follows::

    ❯ slurmhelper genscripts --cluster tmp --spec rshrfmatlab
    Runhelper will run the genscripts operation.
    no job range provided, so writing ALL the scripts.
    Writing job 1 run script to /tmp/slurmhelper_testing/running/scripts/jobs/00001_run.sh
    Writing job 1 copy script to /tmp/slurmhelper_testing/running/scripts/jobs/00001_copy.sh
    Writing job 1 clean script to /tmp/slurmhelper_testing/running/scripts/jobs/00001_clean.sh
    Writing job 2 run script to /tmp/slurmhelper_testing/running/scripts/jobs/00002_run.sh
    Writing job 2 copy script to /tmp/slurmhelper_testing/running/scripts/jobs/00002_copy.sh
    Writing job 2 clean script to /tmp/slurmhelper_testing/running/scripts/jobs/00002_clean.sh
    Writing job 3 run script to /tmp/slurmhelper_testing/running/scripts/jobs/00003_run.sh
    Writing job 3 copy script to /tmp/slurmhelper_testing/running/scripts/jobs/00003_copy.sh
    Writing job 3 clean script to /tmp/slurmhelper_testing/running/scripts/jobs/00003_clean.sh

I check they look good::

    ❯ cat /tmp/slurmhelper_testing/running/scripts/jobs/00001_run.sh
    #!/bin/bash -e

    echo "Begin running job 00001, corresponding to:"
    echo "Subject NDARINVFBE9UXHG, Session baselineYear1Arm1, Task rest, Run 2"
    echo "-----------------------------"

    rshrfmatlab --nthreads 8 --mem_mb 15000 --trim_amt 8 --trim_tgt 375 \
        --participant_label NDARINVFBE9UXHG --session_label baselineYear1Arm1 \
        --task-id rest --run-id 2 --fd_thr 0.3 --tr 0.8 --serial-corr "AR(1)" \
        --basis_functions sfir canontdd \
        --keep_deconv roi \
        --atlas-parametermaps craddock400 shen268 \
        --atlas-deconv craddock400 shen268 \
        --keep_non_olrm \
        /software/matlab-2020b-el7-x86_64/bin/matlab \
        /home/fcmeyer/scratch-midway2/spm12 \
        /tmp/slurmhelper_testing/running/inputs/00001/derivatives \
        /project2/abcd/derivatives/restingstatehrf/restingstatehrf \
        /tmp/slurmhelper_testing/running/work/00001

    exit_status=$?

    echo "exit status: $exit_status"

    if [ $exit_status -eq 0 ]
    then
        echo "it appears things went well, go ahead and rm work and input dirs from scratch"
        rm -rf /tmp/slurmhelper_testing/running/work/00001
        rm -rf /tmp/slurmhelper_testing/running/inputs/00001/derivatives
        echo "SUCCESS"
        echo $exit_status
        exit 0
    else
        echo "it appears things did not go well. we wont touch nothing"
        echo "FAILURE"
        echo $exit_status
        exit 1
    fi

Ok, they do. So now, I go on to the next step.

Creating sbatch array
---------------------

I now prepare an array of jobs, which will have each sbatch array job comprise two user jobs::

    ❯ slurmhelper prep-array --cluster tmp --spec rshrfmatlab --ids 1 2 3 --n_parcels 2 --sbatch_id 1
    Runhelper will run the prep-array operation.
    A total of 3 jobs will be affected by this call.
    ========== BEGIN DOING STUFF ==========
    Submission script written to /tmp/slurmhelper_testing/running/scripts/slurm/sb-0001-100.sh
    ========== TOTALLY DONE! YEE HAW :) ==========
    ========== BEGIN DOING STUFF ==========
    Submission script written to /tmp/slurmhelper_testing/running/scripts/slurm/sb-0001-101.sh
    ========== TOTALLY DONE! YEE HAW :) ==========
    Submission script written to /tmp/slurmhelper_testing/running/scripts/slurm/sb-0001.sh


This is what my file structure looks like now::

    .
    └── running
        ├── checks
        ├── inputs
        ├── logs
        │   ├── jobs
        │   └── slurm
        ├── scripts
        │   ├── jobs
        │   │   ├── 00001_clean.sh
        │   │   ├── 00001_copy.sh
        │   │   ├── 00001_run.sh
        │   │   ├── 00002_clean.sh
        │   │   ├── 00002_copy.sh
        │   │   ├── 00002_run.sh
        │   │   ├── 00003_clean.sh
        │   │   ├── 00003_copy.sh
        │   │   └── 00003_run.sh
        │   └── slurm
        │       ├── sb-0001-100.sh
        │       ├── sb-0001-101.sh
        │       └── sb-0001.sh
        └── work

    10 directories, 12 files

Note, that as indicated in the other parts of the docmentation, to **run** this I would type::

    sbatch running/scripts/slurm/sb-0001.sh

To understand why, let's inspect each file.

The ``sb-0001.sh`` file has the sbatch parameters. It will then iterate over each serial sbatch job,
named appropriately as ``sb-0001-<array_id>.sh`` (I have chosen to start everything at 100 for simplicity)::

    ❯ cat sb-0001.sh
    #!/bin/bash -e

    #SBATCH --job-name=sb-0001
    #SBATCH --output=/tmp/slurmhelper_testing/running/logs/slurm/sb-0001-%a.txt
    #SBATCH --partition=broadwl
    #SBATCH --nodes=1
    #SBATCH --ntasks-per-node=8
    #SBATCH --mem=16000
    #SBATCH --time=0:58:0
    #SBATCH --array=100-101

    # sanity checks
    echo "SLURM_JOBID: " $SLURM_JOBID
    echo "SLURM_ARRAY_TASK_ID: " $SLURM_ARRAY_TASK_ID
    echo "SLURM_ARRAY_JOB_ID: " $SLURM_ARRAY_JOB_ID

    bash /tmp/slurmhelper_testing/running/scripts/slurm/sb-0001-$SLURM_ARRAY_TASK_ID.sh

    exit

By calling sbatch on this file, two jobs will be created, with equal parameters, pointing to the following two scripts.
These are::

    ❯ cat sb-0001-100.sh
    #!/bin/bash -e

    # load necessary modules
    module load python
    module load matlab/2020b
    module load fsl/6.0.4
    module load afni/21.0

    source activate /home/fcmeyer/scratch-midway2/rshrfmatlab

    echo "~~~~~~~~~~~~~ BEGIN SLURM JOB ~~~~~~~~~~~~~~"


    bash /tmp/slurmhelper_testing/running/scripts/jobs/00001_run.sh 2>&1 | tee /tmp/slurmhelper_testing/running/logs/jobs/00001.txt

    echo "~~~~~~~~~~~~~ END SLURM JOB ~~~~~~~~~~~~~~"

    exit

and::

    ❯ cat sb-0001-101.sh
    #!/bin/bash -e

    # load necessary modules
    module load python
    module load matlab/2020b
    module load fsl/6.0.4
    module load afni/21.0

    source activate /home/fcmeyer/scratch-midway2/rshrfmatlab

    echo "~~~~~~~~~~~~~ BEGIN SLURM JOB ~~~~~~~~~~~~~~"


    bash /tmp/slurmhelper_testing/running/scripts/jobs/00002_run.sh 2>&1 | tee /tmp/slurmhelper_testing/running/logs/jobs/00002.txt
    bash /tmp/slurmhelper_testing/running/scripts/jobs/00003_run.sh 2>&1 | tee /tmp/slurmhelper_testing/running/logs/jobs/00003.txt

    echo "~~~~~~~~~~~~~ END SLURM JOB ~~~~~~~~~~~~~~"

    exit

As you can see, array index 1 serially runs user job with id 1, and array index 2 serially runs user
jobs with ids 2 and 3.
