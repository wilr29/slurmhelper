To-dos
======

1. Need a better database management system. Specfically, would like to see:
    - A system for storing a spec, and retrieving it, upon calling the command. This database would be stored within the working direcotry. Reduces need for user to input spec/db name constantly and manually.
    - A system for storing links between ``sbatch_id``, ``job_id``, ``slurm_id``, and ``sbatch_array_element_id``. In other words: I want the user to easily know what user jobs go in which slurm bundle (the ``slurm_id`` and ``job_id`` relation), what that ``slurm_id`` showing as in ``squeue``, and if and how many array elements the ``slurm_id`` (sbatch job) has. This would allow then for one to directly assess batch-specific metrics, and reduce the onus on user to track sbatch_ids, which is currently not well done.
    - A system for updating a spec and tracking which job is generated with what spec (or updating a job to a new spec). Might be applicable e.g. in cases where some subset of jobs need more time, etc.

2. Need a better CLI management thing.
    - Perhaps an interactive wizard would be good. E.g., guiding user through setup, running jobs, updating, etc.
    - Perhaps a system for storing 'config' within the WD, so that this can be frozen and stable, and easily accessible
    - Less commands, make it more parsimonious. There's too many features and options! Users need a clear guide on how to do this.

3. Testing class and methods.
    - Some means of using e.g., pytest, for writing tests that users can use and run easily.
    - A simple guide and framework for impelemnting this. E.g., maybe a tests directory is created in the wd, and whatever scripts people throw in there are completed...

4. A means of generating easily readable report on crashes.
    - E.g., run nipypecli crash on all crash files, aggregate to HTML. Or displaying, outputs, inputs, logs, etc. in a neat thing. Kinda like nipype does, but make it pretty and user friendly.

5. Better documentation (lol)