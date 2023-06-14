import json
import pathlib
import subprocess
import os
class Runner:
    def __init__(self, file_name : str, manifest_file : str) -> None:
        self.file_name = file_name
        self.manifest_file = manifest_file
        self.manifest={}
        self.build_data = {}
        self.working_directory = os.getcwd()

    def run(self)-> None:
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
    
    def _get_base_details(self, ) -> None:
        try : 
            self.build_command = self.build_data["build_command"]
            self.build_directory = self.build_data["build_directory"]
            self.root_directory = self.build_data["root_directory"]
            self.project_dirs = self.build_data["project_dirs"]
            self.project_files = self.build_data["project_files"]
            self.pre_build = self.build_data["pre_build"]
        except KeyError as e:
            print(f"KeyError: {e}")
            raise e
        

    def _build_project_folders(self)-> None:
        pathlib.Path(self.root_directory).mkdir(parents=True, exist_ok=True)
        pathlib.Path(f"{self.root_directory}/build").mkdir(parents=True, exist_ok=True)

        for project_dir in self.project_dirs:
            pathlib.Path(self.root_directory, project_dir).mkdir(parents=True, exist_ok=True)
    def _pre_build(self ) -> None:
        if self.pre_build:
            print(f"running {self.pre_build}")
            os.chdir(f'{self.working_directory}/{self.build_data["root_directory"]}/{self.build_data["build_directory"]}')
            subprocess.run(self.pre_build, shell=True)


    def _create_project_files(self)-> None:
        for project_file in self.project_files:
            pathlib.Path(self.root_directory, project_file).touch(exist_ok=True)

    def _load_manifest(self, manifest_file : str) -> None:
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

    def _process_build_steps(self) -> None:
        for step in self.build_data["steps"]:
            for file,tag in step["add"].items():
                with open(f"{self.working_directory}/{self.root_directory}/{file}", "a") as f:
                    f.write(self.manifest[tag])
            for file,tag in step["replace"].items():
                with open(f"{self.working_directory}/{self.root_directory}/{file}", "w") as f:
                    f.write(self.manifest[tag])
            self._build()
            os.chdir(f'{self.working_directory}/{self.build_data["root_directory"]}/{self.build_data["build_directory"]}')
            data=subprocess.run(step["run"], shell=True)



    def _build(self) -> None:
        print(f"running {self.build_command}")
        os.chdir(f'{self.working_directory}/{self.build_data["root_directory"]}/{self.build_data["build_directory"]}')
        subprocess.run(self.build_command, shell=True)
