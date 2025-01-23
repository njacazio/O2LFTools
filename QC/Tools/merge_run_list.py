#!/usr/bin/env python3

"""
Script to merge run list from a HL train
"""

from download_hyperloop_per_run import get_run_per_run_files


def merge_run_list(hyperloop_train_id, runs):
    hl = get_run_per_run_files(train_id=hyperloop_train_id)
    list_to_merge = []
    for i in hl:
        if str(i.get_run()) in runs:
            print("Adding", i)
            list_to_merge.append(i)
        if len(list_to_merge) == len(runs):
            break
        print(i)

    merge_command = f"hadd /tmp/merged_hl{hyperloop_train_id}_{'_'.join(runs)}.root"
    for i in list_to_merge:
        merge_command += f" {i.out_filename()}"
    print(merge_command)


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("hyperloop_train_id",
                        help="Train ID to consider",
                        type=int)
    parser.add_argument("--runs", "-r",
                        help="Run number to consider")
    args = parser.parse_args()
    runs = args.runs.split(",")
    print(runs)
    merge_run_list(args.hyperloop_train_id, runs=runs)


if __name__ == "__main__":
    main()
