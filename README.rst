slurmhelper
===========

|docs|

**This is a tool currently in active development. Expect chaos and frequent changes!**

``slurmhelper`` is a python command line tool to facilitate running large job arrays on a HPC that uses the `Slurm
Workload Manager <https://slurm.schedmd.com/documentation.html>`_ to manage job submissions.

``slurmhelper`` can be adapted to various use cases and type of jobs. It was originally designed with neuroimaging
processing tasks in mind, but is amenable to whatever use case you may have in mind. Users may customize
``slurmhelper`` to their needs by drafting their own :term:`spec file`.

Requirements
------------

- python == 3.9
- numpy == 1.21.2
- pandas == 1.2.4
- PyYAML == 6.0
- progressbar2 == 4.0.0

Installation
------------

Assuming you have git in your machine, you may install the latest version
to your python environment using pip::

    pip install git+https://github.com/fcmeyer/slurmhelper


If you plan to alter the code or add new features, you may want to clone the
repository and install in editable mode using pip::

    git clone https://github.com/fcmeyer/slurmhelper.git
    cd slurmhelper
    python -m pip install -e .



.. |docs| image:: https://readthedocs.org/projects/slurmhelper/badge/?version=latest
   :target: https://slurmhelper.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status