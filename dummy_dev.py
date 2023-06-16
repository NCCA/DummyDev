#!/usr/bin/env python

import os
import argparse
import runner


def run(file_name: str, manifest_file: str, random_time: int, iterations: int) -> None:
    here = os.getcwd()
    for _ in range(iterations):
        runner.Runner(file_name, manifest_file, random_time).run()
        os.chdir(here)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run a build process usage dummy_dev.py <build_file> <manifest_file>"
    )
    parser.add_argument(
        "--random_time",
        "-r",
        action="count",
        default=0,
        help="add random sleeps to the build steps",
    )
    parser.add_argument(
        "--iterations", "-i", default=1, type=int, help="number of iterations"
    )
    parser.add_argument("files", nargs=argparse.REMAINDER)

    arguments = parser.parse_args()
    if len(arguments.files) != 2:
        parser.print_help()
        exit(1)

    run(
        arguments.files[0],
        arguments.files[1],
        arguments.random_time,
        arguments.iterations,
    )
