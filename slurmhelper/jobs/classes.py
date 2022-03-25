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
        assert isinstance(self._jd, dict), "Invalid data structure"
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
        assert isinstance(value, str), "Can only set as str"
        self._scripts["run"] = value

    @script_copy.setter
    def script_copy(self, value):
        assert isinstance(value, str), "Can only set as str"
        self._scripts["copy"] = value

    @script_clean.setter
    def script_clean(self, value):
        assert isinstance(value, str), "Can only set as str"
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
                "These are: %s" % (" ".join(["'{s}'".format(s=s) for s in fields_rm]))
            )

        dd = copy.deepcopy(self._jd)

        if len(fields_rm) > 0:
            for key in fields_rm:
                dd.pop(key, None)

        return dd

    def _compute_specific_script(self, operation, script_template, verbose):
        logger.info("Job %s: computing script %s" % (self.id, operation))

        # compute fields required by the template provided
        fields = list(
            set([i[1] for i in Formatter().parse(script_template) if i[1] is not None])
        )
        logger.debug(
            "Template for %s requires %d unique parameters:  %s"
            % (operation, len(set(fields)), " ".join(list(set(fields))))
        )

        # Generate a dictionary with required parameters only
        fmt_dict = self._clean_params(fields, verbose)
        # Sanity check
        assert set(fmt_dict.keys()) == set(fields), (
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

        logging.info("Job %d: Successfully computed %s script!" % (self.id, operation))
        logging.debug("Resulting script:\n %s" % (rs))

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

        assert isinstance(config, dict), "Config should be a dict object!"

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
        assert p.exists(), "target folder does not exist! ensure you initialize dir !"
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
        to_write = [k for k in self._scripts.keys() if self._scripts[k] is not None]
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
        results = [
            self._tests_results[test]["result"] for test in self._tests_results.keys()
        ]
        self.is_valid = all(results)
        return

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
        return

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
        return

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
        return

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
        return

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
