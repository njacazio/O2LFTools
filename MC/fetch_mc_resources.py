#!/usr/bin/env python3


import inspect
import subprocess


class bcolors:
    # Colors for bash
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    BOKBLUE = BOLD + OKBLUE
    OKGREEN = "\033[92m"
    BOKGREEN = BOLD + OKGREEN
    WARNING = "\033[93m"
    BWARNING = BOLD + WARNING
    FAIL = "\033[91m"
    BFAIL = BOLD + FAIL
    ENDC = "\033[0m"


def vmsg(*args, color=bcolors.OKBLUE):
    print("** ", color, *args, bcolors.ENDC)


def msg(*args, color=bcolors.BOKBLUE):
    print(color, *args, bcolors.ENDC)


DRY_MODE_RUNNING = False


def run_cmd(cmd, print_output=True):
    vmsg("Running command:", f"`{cmd}`")
    cmd = cmd.split()
    if DRY_MODE_RUNNING:
        msg("Dry mode!!!")
        return
    if "capture_output" in inspect.signature(subprocess.run).parameters:
        # Python 3.7+
        run_result = subprocess.run(cmd, capture_output=True)
    else:
        run_result = subprocess.run(cmd)
    if print_output:
        if run_result.stdout is not None:
            vmsg("stdout:", run_result.stdout.decode('ascii'))
        if run_result.stderr is not None:
            vmsg("stderr:", run_result.stderr.decode('ascii'))
    return run_result


def extract_time(logfile="logtmp_3047049637.txt"):
    print("Input file", logfile)
    results = run_cmd(f"cat {logfile}", print_output=False)
    times = []
    events = None
    for i in results.stdout.decode('ascii').split("\n"):
        if "Launching task: ${O2_ROOT}/bin/o2-sim -e TGeant4 --skipModules ZDC" in i:
            events = i
            break
    print(events)
    if events is None:
        print("Found no events!")
        return None, None
    events = events.split("--skipModules ZDC -n ")[1].split(" ")[0]
    events = int(events)
    for i in results.stdout.decode('ascii').split("\n"):
        if "success" in i:
            t = i.strip("*").strip(" ").strip(")").split(" ")[-1].replace("s", "")
            t = float(t)
            times.append(t)
    print(logfile, times, sum(times), "seconds")
    return sum(times), events
# extract_time()


n_events_from_pipeline = None


def extract_time_pipeline(logfile="pipeline_action.txt"):
    global n_events_from_pipeline
    if n_events_from_pipeline == None:
        n_events_from_pipeline = int(input("Number of events in the pipeline? "))
        vmsg("Number of events in the pipeline", n_events_from_pipeline)
    with open(logfile) as f:
        lines = f.readlines()
        times = []
        for i in lines:
            if "global_runtime" not in i:
                continue
            times.append(i.split("global_runtime : ")[1].strip().strip("s"))
            times[-1] = float(times[-1])
    return sum(times), n_events_from_pipeline


def extract_efficiency(pipeline_file="pipeline_metric.txt"):
    import os
    o2dpg = os.path.expandvars("${O2DPG_ROOT}")
    if o2dpg == "":
        print("O2DPG_ROOT not set")
        return 0, 0
    out = run_cmd(f"{o2dpg}/MC/utils/o2dpg_sim_metrics.py stat -p {pipeline_file}",
                  print_output=False)
    out = out.stdout.decode("ascii").split("\n")
    runtime = None
    efficiency = None
    for i in out:
        if "CPU-efficiency" in i:
            efficiency = float(i.split(":")[1].strip())
        if "Estimated runtime" in i:
            runtime = float(i.split(":")[1].strip())
    return efficiency, runtime


def main(alien_path=None,
         parallel_workers=8,
         log_file_type="pipeline_action",
         max_files=-1,
         compute_efficiency=True):

    if alien_path is None or alien_path == "" or alien_path == "None":
        vmsg("List of MCs to check:")
        out = run_cmd("alien_ls selfjobs", print_output=False).stdout.decode('ascii')
        for i in out.split("\n"):
            if i == "":
                continue
            print(i)
        return

    # Get the home
    alien_home = run_cmd("alien_home", print_output=False)
    alien_home = alien_home.stdout.decode('ascii').strip()
    print("Alien home", alien_home)
    if not alien_path.startswith("selfjobs"):
        alien_path = "selfjobs/"+alien_path
    if not alien_path.startswith("/alice"):
        alien_path = alien_home + alien_path
    results = run_cmd("alien_find alien://"+alien_path+"/*/"+log_file_type+"*", print_output=False)
    results_metric = None
    if compute_efficiency:
        results_metric = run_cmd("alien_find alien://"+alien_path+"/*/pipeline_metric*", print_output=False)

    # Check how many hits
    log_files_found = []
    metric_files_found = []
    for i in results.stdout.decode('ascii').split("\n"):
        if log_file_type not in i:
            continue
        if max_files > 0 and len(log_files_found) > max_files:
            break
        log_files_found.append(i)
    if results_metric is not None:
        for i in results_metric.stdout.decode('ascii').split("\n"):
            if "pipeline_metric" not in i:
                continue
            if max_files > 0 and len(metric_files_found) > max_files:
                break
            metric_files_found.append(i)

    if len(log_files_found) == 0:
        print("No logs found")
        return

    import os
    out_directory = "/tmp/runlogs/"
    out_directory = os.path.join(out_directory, alien_path.strip("/").split("/")[-1])
    os.makedirs(out_directory, exist_ok=True)

    def download_file(full_alien_path, target_path):
        local_file = os.path.join(target_path, full_alien_path.split("/")[-1])
        if os.path.isfile(local_file):
            files.append(local_file)
            return local_file

        if 0:  # Check the stats
            r = run_cmd(f"alien_stat alien://{full_alien_path}", print_output=True)
            if r.returncode != 0:
                print("File not found")
                return
        run_cmd(f"alien_cp alien://{full_alien_path} file:{target_path}", print_output=False)
        return local_file

    files = []
    aods = {}
    for i in log_files_found:
        if i == "":
            continue
        f = download_file(i, out_directory)
        aods[f] = i.replace(i.split('/')[-1], "AO2D.root")
        files.append(f)

    job_efficiency = []
    if compute_efficiency:
        for i in metric_files_found:
            if i == "":
                continue
            f = download_file(i, out_directory)
            eff_file = f+"efficiency"
            if os.path.isfile(eff_file):
                with open(eff_file) as eff_file:
                    l = eff_file.readline()
                    job_efficiency.append((float(l.split(" ")[0]), float(l.split(" ")[1])))
            else:
                job_efficiency.append(extract_efficiency(f))
                with open(eff_file, "w") as eff_file:
                    eff_file.write(f"{job_efficiency[-1][0]} {job_efficiency[-1][1]}")
        # print("Job efficiency", job_efficiency)
        average_efficiecny = sum([i[0] for i in job_efficiency])/len(job_efficiency)
        average_runtime = sum([i[1] for i in job_efficiency])/len(job_efficiency)
        print("Average efficiency", f"{average_efficiecny*100}%", "Average runtime", average_runtime)

    sizes = []
    if 1:
        for f in aods:
            sizefile = f+"size"
            if os.path.isfile(sizefile):
                with open(sizefile) as sizefile:
                    for j in sizefile:
                        sizes.append(float(j))
                        break
                    continue
            i = aods[f]
            r = run_cmd(f"alien_stat alien://{i}", print_output=False)
            r = r.stdout.decode("ascii").split("\n")
            for j in r:
                if "Size:" not in j:
                    continue
                s = j.replace("Size: ", "").replace("(", "").replace(")", " ").split(" ")[0]
                s = float(s)
                sizes.append(s)
                with open(sizefile, "w") as sizefile:
                    sizefile.write(f"{s}")
                break

    total_events = 0
    total_time = 0.0
    n_jobs = 0
    for i in files:
        if "pipeline_action" in log_file_type:
            t, e = extract_time_pipeline(i)
        else:
            t, e = extract_time(i)
        if t is None:
            continue
        total_time += t
        total_events += e
        n_jobs += 1
    total_time_per_event = total_time/total_events
    while 1:
        try :
            target_events = None
            while (target_events is None or (not target_events.isdigit())):
                target_events = input("Number of target events? ")
                target_events = target_events.strip()
                if target_events.endswith("M"):
                    target_events = target_events.strip("M")
                    target_events = target_events + "000000"

            target_events = int(target_events)
            vmsg("Target events", target_events, target_events*1e-6, "M")

            vmsg("In total", total_events, "events in", total_time, "seconds. Time per event", total_time_per_event, "seconds")
            vmsg("*****")
            vmsg(f"{target_events} target events, {target_events/1e6} M", )
            vmsg("*****")
            target_time = total_time_per_event*target_events
            seconds_in_day = 24*60*60

            target_time_days = target_time/(seconds_in_day)
            vmsg("Expected time", target_time, "seconds", target_time_days, "days")
            vmsg("Total time per event", total_time_per_event*target_events/parallel_workers*n_jobs/10000/(seconds_in_day), "days at 10k CPUs")
            target_size = sum(sizes) / total_events * target_events
            vmsg("Expected size", target_size/1e6, "MB", target_size/1e9, "GB", target_size/1e12, "TB")
            vmsg(" ")
            typical_days_at10kcpu_per_event_pbpb = 152/1e8
            vmsg("Typical time per event", typical_days_at10kcpu_per_event_pbpb, "days for PbPb ->",
                target_events*typical_days_at10kcpu_per_event_pbpb,
                "days at 10k CPUs")
            typical_days_at10kcpu_per_event_pp = 4/1e8
            vmsg("Typical time per event", typical_days_at10kcpu_per_event_pp, "days for pp ->",
                target_events*typical_days_at10kcpu_per_event_pp,
                "days at 10k CPUs")
            print("\n")
            print("ctrl+c to exit")
        except KeyboardInterrupt:
            print("\nFarewell!")
            break


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Fetch MC resources and estimate time')
    parser.add_argument('alien_path', type=str, default=None,
                        help='Alien path to the logs', nargs="?")
    parser.add_argument('--parallel_workers', "-p", type=int, default=8,
                        help='Number of parallel workers')
    parser.add_argument('--max_files', "-m", type=int, default=-1,
                        help='Max files to check')
    parser.add_argument('--logfile', "-l", choices=["pipeline_action", "logtmp"], default="pipeline_action",
                        help='Number of parallel workers')
    args = parser.parse_args()
    main(alien_path=args.alien_path,
         parallel_workers=args.parallel_workers,
         max_files=args.max_files,
         log_file_type=args.logfile)
