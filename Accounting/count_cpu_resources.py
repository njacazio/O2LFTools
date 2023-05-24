#!/usr/bin/env python3


"""
Script to extract the CPU needs of a MC
"""


def compute(nevents=110000, subjobs=110, cpu_days=32, output_size_gb=6.4, target=20e6):
    number_of_events_per_job = nevents / subjobs
    time_per_event = cpu_days * 24 * 3600 / nevents
    print(f"Number of events per job: {number_of_events_per_job}")
    cpu_time_per_10k_cpus = time_per_event * target / 10000
    print("Per 10k CPUs", cpu_time_per_10k_cpus / 3600/24, "days.", "Output size", output_size_gb/nevents*target, "GB")


def main():
    nevents = input("How many events? ")
    subjobs = input("How many subjobs? ")
    cpu_days = input("How many CPU days? ")
    output_size_gb = input("How many GB of output? ")
    while True:
        target = input("How many events in total? (CTR+C to exit) ")
        compute(nevents=float(nevents), subjobs=float(subjobs), cpu_days=float(cpu_days), output_size_gb=float(output_size_gb), target=float(target))


main()
