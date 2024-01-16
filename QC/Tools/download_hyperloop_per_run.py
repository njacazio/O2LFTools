#!/usr/bin/env python3

"""
Script to download from the path of merged AnalysisResults the corresponding results for the single runs.
It can be used by providing the path on alien of the merged results.
Example usage: `./download_per_run.py TRAIN_ID`
"""

import subprocess
from os import path
import os
import json
import argparse
try:
    from ROOT import TFile, TH1, TF1, TLatex
except:
    raise Exception("Cannot find ROOT, are you in a ROOT enviroment?")
from multiprocessing import Pool
try:
    import tqdm
except ImportError as e:
    print("Module tqdm is not imported.",
          "Progress bar will not be available (you can install tqdm for the progress bar) `pip3 install --user tqdm`")

import sys
import inspect
from utils import draw_nice_canvas, draw_nice_frame

# Modes
VERBOSE_MODE = False
DRY_MODE_RUNNING = False

labels_drawn = []


def draw_label(label, x=0.55, y=0.96, size=0.035, align=21, ndc=True):
    global labels_drawn
    while label.startswith(" ") or label.endswith(" "):
        label = label.strip()
    l = TLatex(x, y, label)
    if ndc:
        l.SetNDC()
    l.Draw()
    l.SetTextAlign(align)
    l.SetTextFont(42)
    l.SetTextSize(size)
    labels_drawn.append(l)
    return l


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
    if VERBOSE_MODE:
        print("** ", color, *args, bcolors.ENDC)


def msg(*args, color=bcolors.BOKBLUE):
    print(color, *args, bcolors.ENDC)


def fatal_msg(*args, fatal_message="Fatal Error!"):
    msg("[FATAL]", *args, color=bcolors.BFAIL)
    raise RuntimeError(fatal_message)


def run_cmd(cmd):
    vmsg("Running command:", f"`{cmd}`")
    cmd = cmd.split()
    if DRY_MODE_RUNNING:
        msg("Dry mode!!!")
        return
    if "capture_output" in inspect.signature(subprocess.run).parameters:
        # Python 3.7+
        run_result = subprocess.run(cmd, capture_output=not VERBOSE_MODE)
    else:
        run_result = subprocess.run(cmd)
    vmsg(run_result)
    return run_result


class HyperloopOutput:
    def __init__(self,
                 json_entry,
                 out_path="/tmp/"):
        self.alien_path = json_entry["outputdir"] + "/AnalysisResults.root"
        if "run" in json_entry:
            self.run_number = json_entry["run"]
        else:
            self.run_number = None
        self.out_path = path.abspath(out_path)
        # ROOT interface
        self.tfile = None
        self.root_objects = {}

    def get_alien_path(self):
        if "alien://" in self.alien_path:
            raise RuntimeError(f"Path {self.alien_path} is already an alien path")
        return "alien://" + self.alien_path

    def local_file_position(self):
        return self.alien_path.replace("alien://", "")

    def get_run(self):
        return self.run_number

    def out_filename(self):
        in_path = self.alien_path
        file_name = path.basename(in_path)
        dir_name = path.dirname(in_path)
        return path.join(self.out_path, dir_name.strip("/"), file_name)

    def exists(self):
        f = self.out_filename()
        check = path.isfile(f)
        if check:
            vmsg("File", f"`{f}`", "already existing")
            return True
        vmsg("File", f"`{f}`", "not existing")
        return False

    def is_sane(self, throw_fatal=True):
        if not self.exists():
            return False
        f = self.out_filename()
        try:
            open(f)
        except:
            if throw_fatal:
                fatal_msg("Cannot open", f)
            return False
        vmsg("File", f"`{f}`", "is sane")
        return True

    def __str__(self) -> str:
        p = f"{self.get_alien_path()}, locally {self.out_filename()}, run {self.get_run()}"
        if self.is_sane():
            p += " (already downloaded and ok)"
        return p

    def __repr__(self) -> str:
        return self.__str__()

    def copy_from_alien(self,
                        write_download_summary=True,
                        overwrite=False,
                        overwrite_summary=True):
        out_path = path.dirname(self.out_filename())
        if not path.isdir(out_path):
            vmsg("Preparing directory", f"`{out_path}`")
            os.makedirs(out_path)
        else:
            vmsg("Directory", f"`{out_path}`", "already present")
        if write_download_summary and (overwrite_summary or not path.isfile(path.join(out_path, "download_summary.txt"))):
            with open(path.join(out_path, "download_summary.txt"), "w") as f:
                f.write(self.get_alien_path() + "\n")
                f.write(f"Run{self.get_run()}\n")
        if not overwrite and self.exists():
            if self.is_sane():
                msg("File", f"`{self.out_filename()}`",
                    "already present, skipping for download")
                return self.out_filename()
            else:
                os.remove(self.out_filename())
                msg("File", self.out_filename(), "was not sane, removing it and attempting second download", color=bcolors.BWARNING)

        msg("Downloading", self.get_alien_path(), "to", self.out_filename())
        cmd = f"alien_cp -q {self.get_alien_path()} file:{self.out_filename()}"
        run_cmd(cmd)
        if self.is_sane():
            return self.out_filename()
        return None

    def open(self):
        if not self.tfile:
            self.tfile = TFile(self.out_filename())
        return self.tfile

    def get(self, name=None):
        if name in self.root_objects:
            return self.root_objects[name]
        f = self.open()
        if name is None:
            f.ls()
            return
        if "/" in name:
            obj = f
            for i in name.split("/"):
                if "List" in obj.ClassName():
                    obj = obj.FindObject(i)
                else:
                    obj = obj.Get(i)
                if not obj:
                    f.ls()
                    raise ValueError(f"{name} not found")

        else:
            obj = f.Get(name)
        if "Direc" in obj.ClassName():
            obj.ls()
        of_interest = ["TH1F"]
        if obj.ClassName() in of_interest:
            pass
            # if f"{self.get_run()}" not in obj.GetTitle():
            #     t = obj.GetTitle()
            #     t = t + " Run " + f"{self.get_run()}"
            #     t = t.strip()
            #     obj.SetTitle(t)
        self.root_objects[name] = obj
        return obj

    def average(self, name):
        h = self.get(name)
        if not h:
            return None
        return h.GetMean(), h.GetMeanError()

    def valueat1(self, name):
        h = self.get(name)
        if not h:
            return None
        if "TEff" in h.ClassName():
            b = h.FindFixBin(1)
            return h.GetEfficiency(b), 0
            return h.GetEfficiency(b), h.GetEfficiencyErrorUp(b)
        b = h.GetXaxis().FindBin(1)
        return h.GetBinContent(b), h.GetBinError(b)

    def functionfit(self, name, option):
        h = self.get(name)
        if not h:
            return None
        if 0:
            can = draw_nice_canvas("fit")
            h.Draw()
            can.Modified()
            can.Update()
            input("Press enter to continue")
        projection_interval = None
        if "TH2" in h.ClassName():
            xrange = option["x_range"].split(", ")
            xrange = [float(i) for i in xrange]
            projection_interval = [h.GetYaxis().GetBinLowEdge(h.GetYaxis().FindBin(xrange[0])),
                                   h.GetYaxis().GetBinUpEdge(h.GetYaxis().FindBin(xrange[1])),
                                   h.GetYaxis().GetTitle()]
            h = h.ProjectionX("tmp", h.GetYaxis().FindBin(xrange[0]), h.GetYaxis().FindBin(xrange[1]))
        fun = TF1(h.GetName()+"functionfit", option["function"])
        for i in enumerate(option["initial_parameters"].split(", ")):
            fun.SetParameter(i[0], float(i[1]))
            if f"par_range{i[0]}" in option:
                par_range = option[f"par_range{i[0]}"].split(", ")
                par_range = [float(i) for i in par_range]
                fun.SetParLimits(i[0], *par_range)
            print(fun.GetParameter(i[0]))
        fun.Print()
        fitrange = option["fit_range"].split(", ")
        fitrange = [float(i) for i in fitrange]
        h.Fit(fun, option["fit_opt"], "", *fitrange)
        if (type(option["show_single_fit"]) is str and option["show_single_fit"] == "true") or (type(option["show_single_fit"]) is not str and option["show_single_fit"]):
            can = draw_nice_canvas("fit", replace=False)
            h.SetBit(TH1.kNoStats)
            h.SetBit(TH1.kNoTitle)
            h.Draw()
            fun.Draw("same")
            if projection_interval is not None:
                draw_label("Projection interval: " + f"{projection_interval[0]:.2f}, {projection_interval[1]:.2f}, {projection_interval[2]}")
            draw_label(h.GetTitle(), 0.77, 0.85)
            draw_label(f"Run {self.get_run()}", 0.25, 0.85)
            can.Modified()
            can.Update()
            input("Press enter to continue")
        return fun.GetParameter(int(option["parameterindex"])), fun.GetParError(int(option["parameterindex"]))

    def draw(self, name, x_range=None, y_range=None, opt=""):
        h = self.get(name)
        if not h:
            return None
        can = draw_nice_canvas(name, replace=False)
        if "TH" in h.ClassName():
            xtit = h.GetXaxis().GetTitle()
            ytit = h.GetYaxis().GetTitle()
        else:
            xtit = "x"
            ytit = "y"
        if x_range is not None and y_range is not None:
            draw_nice_frame(can, x_range, y_range, xtit, ytit)
            opt += "same"
        if "TH" in h.ClassName():
            obj = h.DrawCopy(opt)
        else:
            obj = h.DrawClone(opt)
        if f"{self.get_run()}" not in obj.GetTitle():
            t = obj.GetTitle()
            t = t + " Run " + f"{self.get_run()}"
            t = t.strip()
            obj.SetTitle(t)
        can.Update()
        can.Modified()
        return can

    def fill_histo(self, h, name, quantity="mean", option=None):
        """
        This function fills the histogram h with the quantity specified of the object asked.
        """
        x = f"{self.get_run()}"
        ib = int(h.GetEntries()) + 1
        if h.GetXaxis().GetTitle() == "":
            h.SetBit(TH1.kNoStats)
            h.GetXaxis().SetTitle("Run number")
        ytitle = None
        if h.GetYaxis().GetTitle() == "":
            ytitle = self.get(name).GetTitle()
        h.GetXaxis().SetBinLabel(ib, x)
        if quantity is None:
            y = 0
            ye = 0
        elif quantity == "mean":
            if ytitle is not None:
                ytitle = f"<{ytitle}>"
            y, ye = self.average(name)
        elif quantity == "valueat1":
            if ytitle is not None:
                ytitle = f"Value at 1" + h.GetXaxis().GetTitle()
            y, ye = self.valueat1(name)
        elif quantity == "functionfit":
            if ytitle is not None:
                ytitle = option["treding_title"].strip("\"")
            y, ye = self.functionfit(name, option)
        else:
            raise ValueError(f"Quantity {quantity} not recognized")

        if ytitle is not None:
            h.GetYaxis().SetTitle(ytitle)
        h.SetBinContent(ib, y)
        h.SetBinError(ib, ye)
        return ib

    def __lt__(self, other):
        return self.run_number < other.run_number


def get_run_per_run_files(train_id=126264,
                          alien_path="https://alimonitor.cern.ch/alihyperloop-data/trains/train.jsp?train_id=",
                          out_path="/tmp/",
                          list_merged_files=False,
                          key_file="/tmp/tokenkey_1000.pem",
                          cert_file="/tmp/tokencert_1000.pem"):
    out_name = path.join(out_path, f"HyperloopID_{train_id}.json")
    if not path.isfile(key_file):
        fatal_msg("Cannot find key file", key_file)
    if not path.isfile(cert_file):
        fatal_msg("Cannot find cert file", cert_file)
    if not path.isfile(out_name):
        download_cmd = f"curl --key {key_file} --cert {cert_file} --insecure {alien_path}{train_id} -o {out_name}"
        run_cmd(download_cmd)
    sub_file_list = []
    with open(out_name) as json_data:
        data = json.load(json_data)
        key = "mergeResults" if list_merged_files else "jobResults"
        if key not in data:
            print(data.keys())
            fatal_msg("Cannot find key", key, "in json file", out_name)
        to_list = data[key]
        for i in to_list:
            sub_file_list.append(HyperloopOutput(i, out_path=out_path))
    msg("Found", len(sub_file_list), "files to download")
    if not list_merged_files:
        sub_file_list.sort()
    return sub_file_list


def download_file(i):
    return i.copy_from_alien(overwrite=False)


def process_one_hyperloop_id(hyperloop_train_id=126264,
                             out_path="/tmp/",
                             overwrite=False,
                             tag=None,
                             download_merged=False,
                             jobs=1,
                             key_file="/tmp/tokenkey_1000.pem",
                             cert_file="/tmp/tokencert_1000.pem"):
    # Getting input for single
    l = get_run_per_run_files(train_id=hyperloop_train_id,
                              out_path=out_path,
                              list_merged_files=download_merged,
                              key_file=key_file,
                              cert_file=cert_file)

    downloaded = []
    if jobs > 1:
        with Pool() as pool:
            pool.map(download_file, l)
    else:
        for i in tqdm.tqdm(l, bar_format='{l_bar}{bar:10}{r_bar}{bar:-10b}'):
            downloaded.append(i.copy_from_alien(overwrite=overwrite))
    print("Downloaded for ID", hyperloop_train_id, "=", downloaded)
    return " ".join(downloaded)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("hyperloop_train_ids",
                        help="Train ID to consider",
                        nargs="+",
                        type=int)
    parser.add_argument("--out_path", "-o",
                        default="/tmp/",
                        help="Output path where the download will be located. Default: `/tmp/`")
    parser.add_argument("--verbose", "-v",
                        action="store_true",
                        help="Name of the file used for merge. Default: `Stage_1.xml`")
    parser.add_argument("--drymode", "--dry", "-d",
                        action="store_true",
                        help="Drymode, avoid download and print only messages. Default: `False`")
    parser.add_argument("--overwrite", "-O",
                        action="store_true",
                        help="Overwrite downloaded output, use with caution. Default: `False`")
    parser.add_argument("--tag", "-t",
                        default=None,
                        help="Tag to use to mark the downloaded files. Default: `None`")
    parser.add_argument("--download_merged", "-m", "--merged",
                        action="store_true",
                        help="Flag to enable the download of the merged output file. Default: `False`")
    parser.add_argument("--key_file", "-k",
                        default="/tmp/tokenkey_1000.pem",
                        help="Key file for authentication")
    parser.add_argument("--jobs", "-j",
                        type=int,
                        default=1,
                        help="Parallel jobs to run. Default: `1`")
    parser.add_argument("--cert_file", "-c",
                        default="/tmp/tokencert_1000.pem",
                        help="Certificate file for authentication")
    args = parser.parse_args()
    if args.verbose:
        VERBOSE_MODE = True
    if args.drymode:
        DRY_MODE_RUNNING = True

    files_downloaded = []
    for i in args.hyperloop_train_ids:
        files_downloaded.append(process_one_hyperloop_id(hyperloop_train_id=i,
                                                         out_path=args.out_path,
                                                         jobs=args.jobs,
                                                         overwrite=args.overwrite,
                                                         tag=args.tag,
                                                         download_merged=args.download_merged,
                                                         key_file=args.key_file,
                                                         cert_file=args.cert_file))
    print("Files downloaded:")
    print(" ".join(files_downloaded))


if __name__ == "__main__":
    main()
