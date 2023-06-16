import json
import os
import pathlib
import subprocess
import time
import random
from typing import List

""" This class is the main class that runs the build process as well as loading in 
the manifest file and processing the build steps"""


class Runner:
    def __init__(self, file_name: str, manifest_file: str, add_delay: int) -> None:
        self.file_name = file_name
        self.manifest_file = manifest_file
        self.manifest = {}
        self.build_data = {}
        self.working_directory = os.getcwd()  # where we are
        self.build_directory = ""  # where the build command is run
        self.root_directory = ""  # where the project source lives
        if add_delay:
            self.add_delay = True
        else:
            self.add_delay = False
        self.env=os.environ.copy()
    """This is the main function that runs the build process"""

    def run(self) -> None:
        print(f"loading {self.file_name}")
        with open(self.file_name, "r") as f:
            self.build_data = json.load(f)
        # Initial project setup before running build command
        self._get_base_details()
        # remove the existing project if it exists
        try:
            print(
                f"removing {self.root_directory} {pathlib.Path(self.root_directory).exists()=}"
            )
            if pathlib.Path(self.root_directory).exists():
                os.system(f"rm -rf {self.root_directory}")
        except Exception as e:
            print(f"Exception: {e}")
            pass
        self._build_project_folders()
        self._load_manifest(self.manifest_file)

        # now process the build steps
        self._process_build_steps()

    """get the base details from the json file"""

    def _get_base_details(self) -> None:
        try:
            self.build_command = self.build_data["build_command"]
            self.root_directory = f'{self.build_data["root_directory"]}'
            if self.root_directory.startswith("~"):
                self.root_directory = self.root_directory.replace(
                    "~", os.path.expanduser("~")
                )
                print(self.root_directory)
            if self.root_directory.startswith("./"):
                self.root_directory = self.root_directory.replace(
                    "./", f"{self.working_directory}/"
                )
                print(self.root_directory)
            self.build_directory = (
                f'{self.root_directory}/self.build_data["build_directory"]'
            )
            self.project_dirs = self.build_data["project_dirs"]
            self.pre_build = self.build_data["pre_build"]
            if self.build_data.get("max_sleep") is not None:
                self.max_sleep = int(self.build_data["max_sleep"])
            else:
                self.max_sleep = 0
        except KeyError as e:
            print(f"KeyError: {e}")
            raise e

    """create the project folders"""

    def _build_project_folders(self) -> None:
        print(f"creatingm project {self.root_directory}")
        pathlib.Path(self.root_directory).mkdir(parents=True, exist_ok=True)
        pathlib.Path(f"{self.root_directory}/build").mkdir(parents=True, exist_ok=True)

        for project_dir in self.project_dirs:
            pathlib.Path(self.root_directory, project_dir).mkdir(
                parents=True, exist_ok=True
            )

    """run the pre-build command if it exists"""

    def _pre_build(self) -> None:
        if self.pre_build:
            print(f"running {self.pre_build}")
            os.chdir(f'{self.root_directory}/{self.build_data["build_directory"]}')
            os.system('rm -f CMakeCache.txt')
            subprocess.run(self.pre_build, shell=True, env=self.env)

    """For ease we create the default files for the project"""

    def _add_project_files(self, files: List[str]) -> None:
        for file in files:
            pathlib.Path(self.root_directory, file).touch(exist_ok=True)

    """load in the manifest file and store it in a dictionary 
        parm : manifest_file - the file to load
    """

    def _load_manifest(self, manifest_file: str) -> None:
        print(f"loading {manifest_file}")
        with open(manifest_file, "r") as f:
            manifest_data = f.readlines()
            current_tag = None
            current_text = ""
            for line in manifest_data:
                if line.startswith("@Tag"):
                    if current_tag is not None:
                        self.manifest[current_tag] = current_text.strip()
                    current_tag = line.strip()
                    current_text = ""
                else:
                    current_text += line
            if current_tag is not None:
                self.manifest[current_tag] = current_text.strip()

    """This is the core function that processes the build steps from the json file and the manifest"""

    def _process_build_steps(self) -> None:
        for step in self.build_data["steps"]:
            # create and new files first
            try:
                self._add_project_files(step["create_files"])
            except KeyError as e:
                pass
            if step.get("pre_build") is not None:
                self._pre_build()
            # do the add and replace steps if they exist
            try:
                for file, tag in step["add"].items():
                    with open(f"{self.root_directory}/{file}", "a") as f:
                        f.write(self.manifest[tag] + "\n")
                    if self.add_delay:
                        self._random_delay()
            except KeyError as e:
                pass
            try:
                for file, tag in step["replace"].items():
                    with open(f"{self.root_directory}/{file}", "w") as f:
                        f.write(self.manifest[tag])
                    if self.add_delay:
                        self._random_delay()
            except KeyError as e:
                pass
            # Now files are changed re-build (we can do this as default)
            self._build()
            if self.add_delay:
                self._random_delay()
            # now run the run command if it exists
            try:
                if self.add_delay:
                    self._random_delay()
                os.chdir(f'{self.root_directory}/{self.build_data["build_directory"]}')
                # now run the run command
                for cmd in step["run"]:
                    print(f"running {cmd} in {os.getcwd()}")
                    data = subprocess.run(cmd, shell=True,env=self.env)
            except KeyError as e:
                pass

    """build the project using the build command pass in the json file"""

    def _build(self) -> None:
        print(f"running {self.build_command} in {os.getcwd()}")
        os.chdir(f'{self.root_directory}/{self.build_data["build_directory"]}')

        subprocess.run(self.build_command, shell=True,env=self.env)

    def _random_delay(self) -> None:
        sleep_time = random.randint(0, self.max_sleep) / 1000
        print(f"adding delay of {sleep_time} ms")
        time.sleep(sleep_time)
