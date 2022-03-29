Usage
=====

.. note::
    If you are annoyed with all the repetitive commands, it may be helpful to define an environment variable you can use in your calls to avoid having to remember all this stuff. For example, say you are working with the same spec and working directory. You could define in your ``.bashrc`` file: ``export sh_args="--cluster midway2-scratch --userid fcmeyer --spec-builtin rshrfmatlab:2022-03-16"`` and then just call ``slurmhelper check completion $sh_args --range 1 30``. Future versions might improve this with a config file, etc.

.. autoprogram:: slurmhelper.cli.parser:build_parser()
    :groups:
    :maxdepth: 2