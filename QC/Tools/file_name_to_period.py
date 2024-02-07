#!/usr/bin/env python3


"""
Script to assign filesnames to period
"""

import download_hyperloop_per_run
import argparse
from shutil import copyfile
import os


def main(hyperloop_train,
         copy_with_period=True,
         runs=None,
         merged=False):
    l = download_hyperloop_per_run.get_run_per_run_files(train_id=hyperloop_train,
                                                         list_merged_files=merged)
    list_of_files = []
    for i in l:
        p = i.get_dataset_name()
        if not copy_with_period:
            continue
        r = i.get_run()
        if r is not None:
            if runs is not None:
                print(runs)
                if r not in runs:
                    continue
        l = i.out_filename()
        if l is None:
            continue
        os.makedirs("/tmp/PerPeriods/", exist_ok=True)
        if r is not None:
            p = f"/tmp/PerPeriods/AnalysisResults_{p}_Run{r}.root"
        else:
            p = f"/tmp/PerPeriods/AnalysisResults_{p}.root"
        print(f"Copying {l} to {p}")
        copyfile(l, p)
        list_of_files.append(p)

    print(f"{list_of_files}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("hyperloop_train_ids",
                        help="Train ID to consider",
                        nargs="+",
                        type=int)
    parser.add_argument("--runs", "-r",
                        help="Runs to consider", nargs="+", type=int, default=None)
    args = parser.parse_args()
    for i in args.hyperloop_train_ids:
        main(i,
             runs=args.runs)
