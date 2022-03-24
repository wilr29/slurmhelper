Glossary
========

.. glossary::

    spec file
        Shorthand for "specification file." A YAML file including general run
        parameters, template scripts, expected wall times, and other important
        information used by ``slurmhelper``.

    user job
        A user job is defined as a command that can be run by slurm from based on
        the specification provided, and the job-specific parameters from a given
        row in a CSV file that you provide. There is flexibility on what exactly can
        constitute a "job"; in my case, I consider a "job" as a pipeline that receives
        as input data from one run, of one task, for one session, for one subject.
        Others may define this differently, depending on the use case.

    database
        A CSV file that enumerates jobs and job-specific information. Must include
        (1) a header column, with (2) one column labeled `order_id` that takes
        integer positive values and (3) any additional columns you would like to
        include (e.g., subject, session, task, run, etc.).
