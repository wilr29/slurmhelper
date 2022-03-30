import logging
import pickledb

logger = logging.getLogger("cli")


class SlurmhelperDB:
    """
    Class for interacting with the internal database.
    """

    def __init__(self, dirs):
        """
        Instantiates a SlurmhelperDB object.
        :param dirs: dict, result of the compute_paths() function
        """
        from pathlib import Path

        self.db_file = Path(dirs["base"]) / "database.db"

        if self.db_file.exists():
            logger.info(f"Slurmhelper DB file exists in: {str(self.db_file)}.")
            self.__is_initialized = True
        else:
            logger.info(
                "Slurmhelper DB file does not exist. Make sure you initialize it before moving forward."
            )
            self.__is_initialized = False

    def initialize(self, dirs, job_df, job_spec):
        """
        Creates a pickleDB database from scratch for a given project.
        :param dirs: dict, result of the compute_paths() function
        :param job_df: pandas.DataFrame (contents of CSV file)
        :param job_spec: dict, result of reading YAML file or whatever.
        :return:
        """

        if self.db_file.exists():
            raise FileExistsError(
                "Database file already exists for your project! You should not be initializing a new one."
            )

        # Establish connection to database.
        db = pickledb.load(self.db_file, False)

        # Add a key to store the directory tree map
        db.set("dirs", dirs)

        # Add a key for our dataframe with jobs (already validated by the CLI interface class)
        db.set("job_df", job_df)

        # Add a key for our job spec
        db.set(
            "job_spec", job_spec
        )  # should point to dict with spec, or to the JobSpec class, when finished...

        # Add a key for our job objects
        db.set("job_obj_dict", dict())

        # Add a key for our sbatch jobs
        db.set("sbatch_jobs", dict())

        db.dump()

    def __repr__(self):
        return f"SlurmhelperDB instance for interacting with {self.db_file}"

    def __str__(self):
        return self.__repr__()

    def add_sbatch_job(self, sbatch_id, sbatch_job):
        """
        Add an sbatch job to the dict. One at a time, please!
        :param sbatch_id: sbatch_id (integer?)
        :param sbatch_job: sbatch job object.
        :return:
        """
        # Establish connection to database.
        db = pickledb.load(self.db_file, False)

        if sbatch_id in db.get("sbatch_jobs").keys():
            raise ValueError(
                f"The specified sbatch_id ({sbatch_id}) already exists in the database. "
                f"Aborting operation to avoid adding a duplicate!"
            )

        # TODO: fix this ASAP once SbatchJob is implemented!!!!!!!
        if not isinstance(sbatch_job, str):
            raise ValueError(
                f"You did not provide a valid SbatchJob object to add. Aborting."
            )

        db.dadd("sbatch_jobs", sbatch_job)

        db.dump()

    def add_user_job(self, job):
        """
        Add a user job object to the job database.
        :param job:
        :return:
        """
        pass
