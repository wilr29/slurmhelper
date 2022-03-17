slurmhelper
===========

|docs|

**This is a tool currently in active development. Expect chaos and frequent changes!**

``slurmhelper`` is a python command line tool to facilitate running large job arrays on a HPC that uses the `Slurm
Workload Manager <https://slurm.schedmd.com/documentation.html>`_ to manage job submissions.

``slurmhelper`` can be adapted to various use cases and type of jobs. It was originally designed with neuroimaging
processing tasks in mind, but is amenable to whatever use case you may have in mind. Users may customize
``slurmhelper`` to their needs by drafting their own :term:`spec file`.

.. |docs| image:: https://readthedocs.org/projects/slurmhelper/badge/?version=latest
   :target: https://slurmhelper.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status