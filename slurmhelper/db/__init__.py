"""
Submodule for storing and serializing stuff...
"""


class ProjectDB:
    """
    Will be serialized to project working directory root, as db.pkl.
    Contains all the information used in the project:
    - Job Units database (derived from CSV file)
    - Sbatch Jobs spawned (each one that is "prepped")
    - Specification being used
    """

    def __init__(self):
        self.__spec = None
        self.__sbatch_db = None
        self.__job_unit_db = None


class SbatchDB:
    """
    Contains jobs that have been spawned.
    """

    def __init__(self):
        self.__sb_dict = {}
