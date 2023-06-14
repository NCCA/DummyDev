import json
import os
import pathlib
import subprocess

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

    """This is the main function that runs the build process"""

    def run(self) -> None:
        print(f"loading {self.file_name}")
        with open(self.file_name, "r") as f:
            self.build_data = json.load(f)
        # remove the existing project if it exists
        if pathlib.Path(self.build_data["root_directory"]).exists():
            os.system(f"rm -rf {self.build_data['root_directory']}")

        # Initial project setup before running build command
        self._get_base_details()
        self._build_project_folders()
        self._create_project_files()
        self._load_manifest(self.manifest_file)
        # now process the build steps
        self._pre_build()
        self._process_build_steps()

    """get the base details from the json file"""

    def _get_base_details(self) -> None:
        try:
            self.build_command = self.build_data["build_command"]
            self.root_directory = (
                f'{self.working_directory}/{self.build_data["root_directory"]}'
            )
            self.build_directory = (
                f'{self.root_directory}/self.build_data["build_directory"]'
            )
            self.project_dirs = self.build_data["project_dirs"]
            self.project_files = self.build_data["project_files"]
            self.pre_build = self.build_data["pre_build"]
        except KeyError as e:
            print(f"KeyError: {e}")
            raise e

    """create the project folders"""

    def _build_project_folders(self) -> None:
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
            os.chdir(
                f'{self.working_directory}/{self.build_data["root_directory"]}/{self.build_data["build_directory"]}'
            )
            subprocess.run(self.pre_build, shell=True)

    """For ease we create the default files for the project"""

    def _create_project_files(self) -> None:
        for project_file in self.project_files:
            pathlib.Path(self.root_directory, project_file).touch(exist_ok=True)

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
            # do the add and replace steps if they exist
            try:
                for file, tag in step["add"].items():
                    with open(f"{self.root_directory}/{file}", "a") as f:
                        f.write(self.manifest[tag])
            except KeyError as e:
                pass
            try:
                for file, tag in step["replace"].items():
                    with open(f"{self.root_directory}/{file}", "w") as f:
                        f.write(self.manifest[tag])
            except KeyError as e:
                pass
            # Now files are changed re-build (we can do this as default)
            self._build()
            # now run the run command if it exists
            try:
                os.chdir(
                    f'{self.working_directory}/{self.build_data["root_directory"]}/{self.build_data["build_directory"]}'
                )
                # now run the run command
                data = subprocess.run(step["run"], shell=True)
            except KeyError as e:
                pass

    """build the project using the build command pass in the json file"""

    def _build(self) -> None:
        print(f"running {self.build_command}")
        os.chdir(
            f'{self.working_directory}/{self.build_data["root_directory"]}/{self.build_data["build_directory"]}'
        )
        subprocess.run(self.build_command, shell=True)
