#!/usr/bin/env python3


"""
Script to assign filesnames to run number as tags
"""

import download_hyperloop_per_run
import argparse



def main(hyperloop_train, request_run_number=None):
    l = download_hyperloop_per_run.get_run_per_run_files(train_id=hyperloop_train)
    list_of_files = []
    list_of_runs = []
    for i in l:
        if request_run_number is not None:
            if i.get_run() not in request_run_number:
                continue
        list_of_files.append(i.local_file_position())
        list_of_runs.append(f"\"Run {i.get_run()}\"")
    list_of_files = " ".join(list_of_files)
    list_of_runs = " ".join(list_of_runs)
    print(f"{list_of_files} -t \"{list_of_runs}\"")
    input("Press enter to continue")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("hyperloop_train_ids",
                        help="Train ID to consider",
                        nargs="+",
                        type=int)
    parser.add_argument("--run", "-r",
                        help="Run number to consider",
                        default=None,
                        nargs="+",
                        type=int)
    args = parser.parse_args()
    for i in args.hyperloop_train_ids:
        main(i,
             request_run_number=args.run)
