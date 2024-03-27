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


def main(alien_path="/alice/cern.ch/user/n/njacazio/selfjobs/NucleiTest_-20240326-192013",
         target_events=250000,
         parallel_workers=8):
    results = run_cmd("alien_find alien://"+alien_path+"/*/logtmp*", print_output=False)
    import os
    os.makedirs("/tmp/runlogs/", exist_ok=True)
    files = []
    aods = {}
    for i in results.stdout.decode('ascii').split("\n"):
        print(i)
        if i == "":
            continue
        local_file = f"/tmp/runlogs/{i.split('/')[-1]}"
        aods[local_file] = i.replace(i.split('/')[-1], "AO2D.root")
        if os.path.isfile(local_file):
            files.append(local_file)
            continue
        run_cmd(f"alien_cp alien://{i} file:/tmp/runlogs/", print_output=False)
        files.append(local_file)

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
        t, e = extract_time(i)
        if t is None:
            continue
        total_time += t
        total_events += e
        n_jobs += 1
    total_time_per_event = total_time/total_events
    print("In total", total_events, "events in", total_time, "seconds. Time per event", total_time_per_event, "seconds")
    target_time = total_time_per_event*target_events
    target_time_days = target_time/(24*60*60)
    print("Expected time", target_time, "seconds", target_time_days, "days")
    print("Total time per event", total_time_per_event*target_events*parallel_workers*n_jobs/10000/(24*60*60), "days at 10k CPUs")
    target_size = sum(sizes) / total_events * target_events
    print("Expected size", target_size/1e6, "MB", target_size/1e9, "GB", target_size/1e12, "TB")


main()
