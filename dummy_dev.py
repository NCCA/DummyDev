#!/usr/bin/env python

import os
import runner

def run(file_name : str, manifest_file :str) -> None:
    runner.Runner(file_name,manifest_file).run()


if __name__ == "__main__" :
    run("examples/helloworld.json","examples/helloworld.manifest")