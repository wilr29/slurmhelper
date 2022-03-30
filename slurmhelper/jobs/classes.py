import copy
import glob
import json
import logging
import os
from pathlib import Path
from string import Template, Formatter

logger = logging.getLogger("cli")


class Job:
    """
    Specifies a class for which scripts will be generated.
    """

    # TODO: refactor such that this, Job and TestableJob are all the same base
    #       class.. defined flexibly... And document it better...

    def __init__(self, order_id, dirs, job_dict=None, config=None, verbose=False):
        self.id = order_id
        self._basedirs = dirs
        self._jd = job_dict
        self._scripts = {"run": None, "copy": None, "clean": None}
        self._script_names = {
            "run": "%05d_run.sh" % self.id,
            "copy": "%05d_copy.sh" % self.id,
            "clean": "%05d_clean.sh" % self.id,
        }
        # this adds a bunch of job-specific paths to the job param dict that can be used to fill in
        # a template script! :)
        self.compute_paths(config, verbose)

        self._is_scripted = False

    def __str__(self):
        return "{job:05d}".format(job=self.id)

    def __repr__(self):
        scr_status = ",scripted" if self.is_scripted else ""
        return "Job[{job:05d}{scripted}]".format(job=self.id, scripted=scr_status)

    def __eq__(self, other):  # WARNING! this is only based on ids...
        if isinstance(other, Job):
            return self.id == other.id
        else:
            return False

    def __ne__(self, other):
        return not self == other

    def __gt__(self, other):
        if isinstance(other, Job):
            return self.id > other.id
        else:
            return False

    def __lt__(self, other):
        if isinstance(other, Job):
            return self.id < other.id
        else:
            return False

    def __le__(self, other):
        return self == other or self < other

    def __ge__(self, other):
        return self == other or self > other

    @property
    def is_scripted(self):
        return self._is_scripted

    @is_scripted.setter
    def is_scripted(self, value):
        if not isinstance(self._jd, dict):
            raise AssertionError("Invalid data structure")
        self._is_scripted = value

    @property
    def params(self):
        """
        Get job parameters as dict (augmented).
        Only available if scriptwriter was run.
        :return: dict with parameters
        """
        return self._jd

    @property
    def script_run(self):
        return self._scripts["run"]

    @property
    def script_copy(self):
        return self._scripts["copy"]

    @property
    def script_clean(self):
        return self._scripts["clean"]

    @script_run.setter
    def script_run(self, value):
        if not isinstance(value, str):
            raise AssertionError("Can only set as str")
        self._scripts["run"] = value

    @script_copy.setter
    def script_copy(self, value):
        if not isinstance(value, str):
            raise AssertionError("Can only set as str")
        self._scripts["copy"] = value

    @script_clean.setter
    def script_clean(self, value):
        if not isinstance(value, str):
            raise AssertionError("Can only set as str")
        self._scripts["clean"] = value

    def print_all_params(self):
        """
        Utility function, pretty prints all available job data that can be used for filling
        scripts. Mainly helpful for debugging.
        :return:
        """
        print("Job %s has the following parameters available:\n" % (str(self)))
        print("------------------------------------------")
        print(json.dumps(self.params, sort_keys=False, indent=2))

    def _clean_params(self, fields, verbose):
        fields_rm = list(set([f for f in self._jd.keys() if f not in fields]))

        logger.debug(
            f"From the available {len(self._jd.keys())} job parameters, "
            f"{len(fields_rm)} will be removed for formatting script."
        )
        if len(fields_rm) > 0:
            logger.debug(
                "These are: %s", (" ".join(["'{s}'".format(s=s) for s in fields_rm]))
            )

        dd = copy.deepcopy(self._jd)

        if len(fields_rm) > 0:
            for key in fields_rm:
                dd.pop(key, None)

        return dd

    def _compute_specific_script(self, operation, script_template, verbose):
        logger.info("Job %s: computing script %s", self.id, operation)

        # compute fields required by the template provided
        fields = list(
            set([i[1] for i in Formatter().parse(script_template) if i[1] is not None])
        )
        logger.debug(
            "Template for %s requires %d unique parameters:  %s",
            operation,
            len(set(fields)),
            " ".join(list(set(fields))),
        )

        # Generate a dictionary with required parameters only
        fmt_dict = self._clean_params(fields, verbose)
        # Sanity check
        if set(fmt_dict.keys()) != set(fields):
            raise AssertionError(
                "You're missing information!\n"
                "%d fields supplied: %s\n"
                "%d fields required: %s\n"
                % (
                    len(fmt_dict),
                    " ".join(fmt_dict.keys()),
                    len(set(fields)),
                    " ".join(list(set(fields))),
                )
            )

        # Fill in my template!
        logging.debug("Attempting to format script template using safe substitution...")
        rs = Template(script_template).safe_substitute(fmt_dict)

        logging.info("Job %d: Successfully computed %s script!", self.id, operation)
        logging.debug("Resulting script:\n %s", (rs))

        if operation == "run":
            self.script_run = rs
        elif operation == "copy":
            self.script_copy = rs
        elif operation == "clean":
            self.script_clean = rs
        else:
            raise ValueError("Invalid operation proposed!")

    def compute_scripts(self, config, verbose=False):
        """
        compute script thingys
        :param config: config dict returned from yaml file. need keys: (a) run_script; (b) copy_script; (c) clean_script
        :param verbose: whether to print extra output (default=False)
        :return:
        """

        if not isinstance(config, dict):
            raise AssertionError("Config should be a dict object!")

        cnt = 0
        if "run_script" in config.keys():
            self._compute_specific_script("run", config["run_script"], verbose)
            cnt = +1

        if "copy_script" in config.keys():
            self._compute_specific_script("copy", config["copy_script"], verbose)
            cnt = +1

        if "clean_script" in config.keys():
            self._compute_specific_script("clean", config["clean_script"], verbose)
            cnt = +1

        if cnt > 0:
            self.is_scripted = True

        return cnt > 0

    def _write(self, operation):
        p = Path(self._basedirs["job_scripts"])  # target path
        if not p.exists():
            raise AssertionError(
                "target folder does not exist! ensure you initialize dir !"
            )
        with open(p.joinpath(self._script_names[operation]), "w") as writer:
            logger.info(
                "Writing job {id} {op} script to {path}".format(
                    id=self.id,
                    op=operation,
                    path=str(p.joinpath(self._script_names[operation])),
                )
            )
            writer.write(self._scripts[operation])

    def write_scripts_to_disk(self):
        to_write = [k for k in self._scripts if self._scripts[k] is not None]
        for op in to_write:
            self._write(op)

    def compute_paths(self, config=None, verbose=False):
        """
        Compute various job-related paths. Extends basedirs with job-specific info.
        :return: dict, with paths.
        """
        bd = self._basedirs
        # add global base dirs to params
        # for base_path in bd.keys():
        #     self._jd['_'.join(['global', base_path])] = bd[base_path]
        # add specific job paths to params
        self._jd["this_job_run_script"] = str(
            Path(bd["job_scripts"]).joinpath(self._script_names["run"])
        )
        self._jd["this_job_copy_script"] = str(
            Path(bd["job_scripts"]).joinpath(self._script_names["copy"])
        )
        self._jd["this_job_clean_script"] = str(
            Path(bd["job_scripts"]).joinpath(self._script_names["clean"])
        )
        self._jd["this_job_log_file"] = str(
            Path(bd["job_logs"]).joinpath("%s.txt" % (str(self)))
        )
        self._jd["this_job_inputs_dir"] = str(
            Path(bd["job_inputs"]).joinpath(str(self))
        )
        self._jd["this_job_work_dir"] = str(Path(bd["job_work"]).joinpath(str(self)))
        # this adds some outputs stuff, useful for cleaning scripts...
        if config is not None:
            if "output_path" in config.keys():
                self._jd["output_base_dir"] = config["output_path"]
                if "output_path_subject" in config.keys():  # requires output_path;
                    subdir = os.path.join(*config["output_path_subject"])
                    subdir_fields = list(
                        set(
                            [
                                i[1]
                                for i in Formatter().parse(subdir)
                                if i[1] is not None
                            ]
                        )
                    )
                    format_dict = {
                        k: v for (k, v) in self.params.items() if k in subdir_fields
                    }
                    self._jd["this_job_output_dir"] = os.path.join(
                        self._jd["output_base_dir"], subdir.format(**format_dict)
                    )
                    if (
                        "output_path_subject_expr" in config.keys()
                    ):  # requires the above two!
                        re_template = config["output_path_subject_expr"]
                        re_fields = list(
                            set(
                                [
                                    i[1]
                                    for i in Formatter().parse(re_template)
                                    if i[1] is not None
                                ]
                            )
                        )
                        format_dict = {
                            k: v for (k, v) in self.params.items() if k in re_fields
                        }
                        self._jd["this_job_output_expr"] = re_template.format(
                            **format_dict
                        )
                        self._jd["this_job_output_expr_fullpath"] = os.path.join(
                            self._jd["this_job_output_dir"],
                            self._jd["this_job_output_expr"],
                        )

    @property
    def has_job_log(self):
        return os.path.exists(self._jd["this_job_log_file"])

    @property
    def ran_successfully(self):
        # assumption: exit code is last line!
        lines = self.read_job_log_lines()
        return lines[-1] == "0"

    def read_job_log_lines(self):
        from ..utils.reporting import read_log_file_lines

        if not self.has_job_log:
            raise FileNotFoundError(
                f"No log file is available for job {self.id} in "
                f"{self._jd['this_job_log_file']}!"
            )

        return read_log_file_lines(self._jd["this_job_log_file"])

    def print_job_log(self, head=6, tail=6, full=False):
        """
        Pretty prints the job log header and footer. Sensitivity optional, shows more
        or less lines.
        :param line_trim: how many lines to show from top and bottom
        :return:
        """
        from ..utils.reporting import pretty_print_log

        pretty_print_log(
            self._jd["this_job_log_file"], head=head, tail=tail, full=full, header="job"
        )


class TestableJob(Job):
    # TODO: separate this code into base, generic class - and augmented version of
    #       it for my specific use case.
    """
    Extends the Job class, with specific tests.

    Initially, this class will serve specifically for the rshrfmatlab project.
    In the future, my hope is to construct a more generic class, than people
    can then enhance with methods addressing their own specific needs / tests.
    """

    def __init__(self, db, paths, order_id, config):
        super(TestableJob, self).__init__(order_id, paths, job_dict=None, config=config)
        self._db_index = db.index[db["order_id"] == self.id]
        self.record = db.iloc[self._db_index].to_dict(orient="records")[0]
        self._tests_ran = False
        self._tests_results = {}
        self.is_valid = False
        self._glob_expr = self.record["glob_output_expr"]
        self._dir_outputs = self.record["output_dir"]
        self._dir_inputs = os.path.join(
            paths["job_work"], "{job:05d}".format(job=self.id)
        )
        self._dir_work = os.path.join(
            paths["job_inputs"], "{job:05d}".format(job=self.id)
        )
        self._path_log = os.path.join(
            paths["job_logs"], "{job:05d}.txt".format(job=self.id)
        )
        self.config = config
        # run tests
        self.run_tests()

    def get_logs(self):
        logs = []
        for test in self._tests_results:
            if not self._tests_results[test]["result"]:
                logs.append(
                    "Test {test}: {log}".format(
                        test=test, log=self._tests_results[test]["logs"]
                    )
                )

        warnings = "; ".join(logs)
        return warnings

    def print_status(self):
        if not self._tests_ran:
            print("{job:05d} has not had tests run yet.".format(job=self.id))
        else:
            if self._is_valid:
                print("{job:05d} was successfully completed. All tests look good.")
            else:
                print("{job:05d} has some problems. See below for detailed results:")
                # TODO: update this to match results parsed or something
                print(self._tests_results)

    def _update_valid(self):
        results = [self._tests_results[test]["result"] for test in self._tests_results]
        self.is_valid = all(results)

    def get_results_list(self):
        return [self.id, self._tests_results]

    def test_check_outputs(self):
        rv = {"result": False, "logs": []}

        if not os.path.isdir(self._dir_outputs):
            rv["logs"].append("Output directory does not exist.")
        else:
            g_list = glob.glob(self._glob_expr)
            if len(g_list) == self.config["expected_n_files"]:
                rv["result"] = True
            else:
                rv["logs"].append(
                    "Number of files found does not match expectation;"
                    " expected = {exp:d}, found = {found:d}".format(
                        exp=self.config["expected_n_files"], found=len(g_list)
                    )
                )

        # Append results to results dict
        self._tests_results["check_outputs"] = rv

    def test_check_inputs(self):
        rv = {"result": False, "logs": []}

        if not os.path.isdir(self._dir_inputs):
            rv["result"] = True
        else:
            rv["logs"].append(
                "Input directory exists at {dir}".format(dir=self._dir_inputs)
            )

        # Append results to results dict
        self._tests_results["check_inputs"] = rv

    def test_check_work(self):
        rv = {"result": False, "logs": []}

        if not os.path.isdir(self._dir_inputs):
            rv["result"] = True
        else:
            rv["logs"].append(
                "Work directory exists at {dir}".format(dir=self._dir_work)
            )

        # Append results to results dict
        self._tests_results["check_work"] = rv

    def test_check_logs(self):
        rv = {"result": False, "logs": []}

        if not os.path.isfile(self._path_log):
            rv["logs"].append(
                "Job log file NOT found at {dir}".format(dir=self._path_log)
            )
        else:
            with open(self._path_log, "r") as logfile:
                log = logfile.read().splitlines()
                if len(log) == 0:
                    rv["logs"].append("Log file is empty.")
                elif len(log) == 1:
                    rv["logs"].append(
                        "Log file is one line long? Weird. Line is:\n{line1}".format(
                            line1=log[0]
                        )
                    )
                elif log[-1] == "0" and log[-2] == "SUCCESS":
                    rv["result"] = True
                else:
                    rv["logs"].append(
                        "Log ending is not as expected. Last two lines are:"
                        "\n{line1}\n{line2}".format(line1=log[-2], line2=log[-1])
                    )

        # Append results to results dict
        self._tests_results["check_log"] = rv

    def get_results_dict(self):
        if not self._tests_ran:
            print("{job:05d} has not had tests run yet.".format(job=self.id))
        else:
            rv = self.record
            rv["valid"] = self.is_valid
            for test in self._tests_results:
                result_key = "result_{test_name}".format(test_name=test)
                log_key = "log_{test_name}".format(test_name=test)
                rv[result_key] = self._tests_results[test]["result"]
                rv[log_key] = " ; ".join(self._tests_results[test]["logs"])
            return rv

    def run_tests(self):
        self.test_check_outputs()
        self.test_check_inputs()
        self.test_check_work()
        self.test_check_logs()

        # update validity if applicable
        self._tests_ran = True
        self._update_valid()


class __SbatchJob:
    """
    Initializes an SbatchJob object
    """

    def __init__(self, sbatch_id: int, spec: dict, dirs: dict, job_list: list):

        self.__sbatch_id = (
            sbatch_id  # an integer; see __str__ definition for nice print
        )
        self.script = None
        self.spec = spec
        self.dirs = dirs
        self.jobs = {str(job): job for job in job_list}

    def __str__(self):
        raise NotImplementedError("Should not be using this class directly!")

    def __repr__(self):
        raise NotImplementedError("Should not be using this class directly!")

    @property
    def script_filename(self):
        return f"sb-{str(self)}.sh"

    @property
    def log_file(self):
        from pathlib import Path

        return Path(self.dirs["slurm_logs"]) / f"{str(self)}.txt"

    @property
    def submitted(self):
        return self.slurm_id is not None

    @property
    def n_jobs(self):
        return len(self.__jobs.keys())

    @property
    def job_ids(self):
        return [job for job in self.__jobs.keys()]

    @property
    def job_list(self):
        """
        Returns a copy of the job objects in here
        :return:
        """
        from copy import deepcopy

        return deepcopy(self.__jobs)

    def __get_arr_line(self):
        """
        Indicates the array line for the sbatch script`
        :return: a string
        """
        raise NotImplementedError(
            "You should not be calling this class directly."
            "Please define this method in your derived classes."
        )

    def __build_script_header(self, args):

        from ..utils.time import calculate_wall_time

        if args.time is not None:  # use manually specified time
            time = args.time
        else:  # calculate wall time using our current assumptions
            time = calculate_wall_time(len(self.jobs.keys()), self.spec)

        # Figure out the log path
        log_out = self.log_file
        hdr = Template(self.spec["header"]).safe_substitute(
            job_name=str(self),
            log_path=log_out,
            n_tasks=args.n_tasks[0],
            mem=args.memory[0],
            time=time,
            job_array=self.__get_arr_line(),
        )
        header_f = "\n".join([hdr, self.spec["preamble"]])

        self._script_header = header_f

    def __build_job_calls(self):
        # Ok, let's create the section where we call each job script.
        script_call = "bash {target_path} 2>&1 | tee {job_log_path}"

        job_calls = []
        for job_id in self.jobs.keys():
            script_name = "{job_id:05d}_run.sh".format(job_id=job_id)
            target_path = os.path.join(self.dirs["job_scripts"], script_name)
            job_log_path = os.path.join(
                self.dirs["job_logs"], "{job_id:05d}.txt".format(job_id=job_id)
            )
            job_calls.append(
                script_call.format(target_path=target_path, job_log_path=job_log_path)
            )

        return "\n".join(job_calls)

    def build_script(self, args):
        header = self.__build_script_header(args)
        job_calls = self.__build_job_calls()

        self.script = "\n\n".join(
            [
                header,
                job_calls,
                '''echo "~~~~~~~~~~~~~ END SLURM JOB ~~~~~~~~~~~~~~"''',
                "exit",
            ]
        )

    def write_script(self):
        if self.script is None:
            raise KeyError("Script has not been generated yet!")
        else:
            tgt_path = Path(self.dirs["slurm_scripts"]) / self.script_filename
            if tgt_path.exists():
                raise FileExistsError(
                    f"A script already exists in the intended write location:"
                    f" {str(tgt_path)}. Please use a different sbatch_id to avoid problems."
                )
            else:
                with open(tgt_path, "w") as f:
                    f.write(self.script)
                    logger.info(f"Wrote file: {tgt_path}")

    def set_up(self, args):
        # If not exist, generate scripts.
        # <CODE>
        # If indicated, do reset/clean/clear
        # <CODE>
        # Build and write wrapper script
        self.build_script(args)
        if "dry" in args and not args.dry:
            self.write_script(args)


class __SubmittableSbatchJob(__SbatchJob):
    """
    Extends SbatchJob with a submit method.
    """

    def __init__(self, sbatch_id: int, spec: dict, dirs: dict, job_list: list):
        super().__init__(sbatch_id, spec, dirs, job_list)

        self.slurm_id = None

    @property
    def submitted(self):
        return self.slurm_id is not None

    def submit(self):
        """
        Helper function to submit sbatch scripts. It does so from a "crashes" file, such that any
        nipype related crash files would dump to a "crashes" directory corresponding to the sbatch submission.
        This hopefully makes debugging a bit easier?
        :param id: sbatch_id (int)
        :param dirs: dirs dictionary generated by calculate_directories.
        :return:
        """
        # Should not run directly on array elements!

        from pathlib import Path
        import subprocess

        if self.array_element:
            raise NotImplementedError(
                "You should NOT be calling this on an array element!"
                " For the moment, a wrapper thingy is not implemented..."
            )

        script_to_submit = (
            Path(self.dirs["slurm_scripts"]) / f"sb-{str(id).zfill(4)}.sh"
        )
        if not script_to_submit.exists():
            raise FileNotFoundError(
                f"Script for sbatch_id {id} not found\n\t(expected: {str(script_to_submit)})"
            )

        from_path = Path(self.dirs["crashes"])
        if not from_path.exists():
            raise FileNotFoundError(
                "Crashes directory not found. Did you initialize this wd correctly?"
            )

        # create directory from which we submit this
        # wd/crashes/sb-####/
        from_path = from_path / f"sb-{str(id).zfill(4)}"
        from_path.mkdir(parents=True, exist_ok=True)

        cmd_output = subprocess.check_output(
            ["sbatch", str(script_to_submit)],
            encoding="UTF-8",
            cwd=str(
                from_path
            ),  # run from the pertinent crashes dir, so things are neat
        )

        # Output looks like this: 'Submitted batch job 18334739\n'
        try:
            slurm_id = cmd_output.strip().replace("Submitted batch job ", "")
        except Exception as err:
            logger.critical(str(err))
            print(err)

        self.slurm_id = slurm_id

        print(
            f"Sbatch job sb-{str(id).zfill(4)}.sh submitted.\n"
            f"The Slurm ID for this job (seen in squeue) is {slurm_id}."
        )


class SbatchStandalone(__SubmittableSbatchJob):
    """
    Extends SubmittableSbatchJob, sets up in such a way that
    it makes it usable for generating scripts, etc.
    """

    def __init__(self, sbatch_id: int, spec: dict, dirs: dict, job_list: list):
        super().__init__(sbatch_id, spec, dirs, job_list)

    @property
    def id(self):
        return self.__id

    def __str__(self):
        return f"{str(self.id).zfill(4)}"

    def __repr__(self):
        return f"StandaloneSbatchJob sb-{self.__str__()}"

    def __get_arr_line(self):
        return ""


class SbatchArrayElement(__SbatchJob):
    def __init__(
        self, sbatch_id: int, spec: dict, dirs: dict, job_list: list, array_index: int
    ):

        super().__init__(sbatch_id, spec, dirs, job_list)

        # Check if it is an array.
        if isinstance(array_index, int):
            self.array_index = array_index
        else:
            raise ValueError(
                f"Array index value should be an integer. "
                f"You provided: {array_index}"
            )

    def __str__(self):
        return "%04d-%d" % self.id

    def __repr__(self):
        return f"SbatchArrayElement sb-{self.__str__()}"

    def __build_script_header(self):
        self._script_heaader = "\n".join(["""#!/bin/bash -e""", self.spec["preamble"]])

    @property
    def id(self):
        return (self.__sbatch_id, self.array_index)


class SbatchArray(__SubmittableSbatchJob):
    def __init__(
        self,
        sbatch_id: int,
        spec: dict,
        dirs: dict,
        job_list: list,
        parallel=50,
        step=None,
    ):
        self.__validate_optional_args(parallel=parallel, step=step)

        super().__init__(sbatch_id, spec, dirs, job_list)

        self.__parallel = parallel
        self.__step = step

        self.__initialize_elements(parallel)

    @property
    def id(self):
        return self.__id

    @property
    def n_elements(self):
        """
        How many sub-sbatchs in array
        :return:
        """
        return len(self.elements.keys())

    @property
    def range(self):
        '''
        Indices for filling in
        :return: tuple, start index, end index
        '''
        return (min(self.elements.keys()), max(self.elements.keys()))

    @property
    def n_jobs(self):
        """
        Total number of job units within array
        :return:
        """
        return sum([self.elements[element].n_jobs for element in self.elements.keys()])

    def __str__(self):
        return f"{str(self.id).zfill(4)}"

    def __repr__(self):
        return f"SbatchArray sb-{self.__str__()} ({self.n_elements} elements)"

    def __validate_optional_args(self, **kwargs):
        for arg in kwargs.keys():
            if kwargs[arg] is not None and not isinstance(kwargs[arg],int):
                raise ValueError(f"Input argument {arg} should be left as None, or be an integer value.")

    def __n_parcels(self, parallel):
        '''
        Identify the optimal number of parcels to use.
        :param strategy: str, one of: {'even','pro_array','pro_serial'}
            - even: attempt to split jobs into parcels that
        :return:
        '''
        from slurmhelper.utils.time import calculate_min_number_of_parcels
        from slurmhelper.utils.misc import find_optimal_n_parcels

        if not isinstance(parallel, int) and parallel >= 0 and parallel <= 100:
            raise ValueError("parallel should be an integer with value between 0 and 100.")

        n_jobs = len(self.jobs.keys())
        n_parcels_min = calculate_min_number_of_parcels(n_jobs, self.spec)
        return find_optimal_n_parcels(n_jobs, n_parcels_min, parallel)

    def __initialize_elements(self, parallel=50):
        """
        Array helper - initializes elements too! :)
        :return:
        """
        from slurmhelper.utils.misc import split_list

        # How many parcels to use?
        n_parcels = self.__n_parcels(parallel)
        element_list = split_list(self.job_list, wanted_parts = n_parcels)

        # Create dict with keys (elements) of length (n_parcels), with sbatchArrayelements in them.
        self.elements = {ind+100 : SbatchArrayElement(sbatch_id=self.sbatch_id, spec=self.spec,
                                                      dirs=self.dirs, job_list=jl, array_index=ind+100)
                         for (ind,jl) in enumerate(element_list)}

    def __get_arr_line(self):
        rv = f"#SBATCH --array={self.start_index}-{self.end_index}"
        if self.__step is not None:
            rv = "%".join([rv, self.__step])
        return rv
