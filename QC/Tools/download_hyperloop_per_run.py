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
    from ROOT import TFile, TH1, TF1, TLatex, gMinuit, TNamed
    import ROOT
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


def msg(*args, color=bcolors.BOKBLUE):
    print(color, *args, bcolors.ENDC)


def vmsg(*args, color=bcolors.OKBLUE):
    if VERBOSE_MODE:
        print("** ", color, *args, bcolors.ENDC)


def wmsg(*args):
    color = bcolors.BWARNING
    print("## ", color, *args, bcolors.ENDC)


def fatal_msg(*args, fatal_message="Fatal Error!"):
    msg("[FATAL]", *args, color=bcolors.BFAIL)
    raise RuntimeError(fatal_message)


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


drawn_objects = []


class HyperloopOutput:
    def __init__(self,
                 json_entry,
                 full_json=None,
                 out_path="/tmp/"):

        self.out_path = path.abspath(out_path)

        def get(key):
            if key in json_entry:
                return json_entry[key]
            return None

        def getgeneral(key):
            if full_json is None:
                return None
            if key in full_json:
                return full_json[key]
            return None

        self.alien_outputdir = get("outputdir")
        self.run_number = get("run")
        vmsg("Adding hyperloop output for run number", self.run_number)
        self.merge_state = get("merge_state")
        if self.merge_state != "done":
            wmsg("Merge state for run", self.run_number, "is", self.merge_state)
            if self.alien_outputdir is not None and self.exists() == False:
                vmsg("Attempting to get partial merged files")
                merge_stages = self.get_merged_stages()
                partial_merge = None
                for i in merge_stages:
                    partial_merge = self.list_partial_merged_files(merge_stage=i)
                    if partial_merge is not None:
                        break
                if partial_merge is not None:
                    wmsg(f"Partial merge for run {self.run_number} found in stage {i}", "getting", partial_merge[-1])
                    partial_merge = self.list_partial_merged_files(merge_stage=partial_merge[-1])
                    partial_merge_file = [i for i in partial_merge if "AnalysisResults.root" in i]
                    self.alien_outputdir += "/"+partial_merge_file[0].strip("AnalysisResults.root")
                    self.alien_outputdir = self.alien_outputdir.replace("//", "/")
                    self.merge_state = "partially_merged"

        self.dataset_name = getgeneral("dataset_name")
        # ROOT interface
        self.tfile = None
        self.root_objects = {}

    def alien_path_analysis_results(self):
        if self.alien_outputdir is not None:
            return self.alien_outputdir + "/AnalysisResults.root"
        return None

    def get_dataset_name(self):
        return self.dataset_name

    def get_merged_stages(self):
        alien_listing = run_cmd(f"alien_ls alien://{self.alien_outputdir}", print_output=False)
        merge_stages = []
        for i in alien_listing.stdout.decode('ascii').split("\n"):
            if "Stage" in i and "/" in i:
                merge_stages.append(i)
        merge_stages.sort()
        merge_stages.reverse()
        return merge_stages

    def list_partial_merged_files(self, merge_stage="Stage_3/"):
        alien_listing = run_cmd(f"alien_ls alien://{self.alien_outputdir}/{merge_stage}", print_output=False)
        alien_listing = alien_listing.stdout.decode('ascii').split("\n")
        alien_listing = [f"{merge_stage}/{i}" for i in alien_listing if i]
        # print(alien_listing)
        if len(alien_listing) == 0:
            return None
        return alien_listing

    def get_alien_path(self):
        if "alien://" in self.alien_path_analysis_results():
            raise RuntimeError(f"Path {self.alien_path_analysis_results()} is already an alien path")
        return "alien://" + self.alien_path_analysis_results()

    def find_derived_data(self, merged_derived_data=True):
        cmd = f"alien_find {self.alien_outputdir} AO2D.root"
        out = run_cmd(cmd)
        found_files = out.stdout
        # print(found_files)
        found_files = found_files.decode('ascii').strip("\n")
        file_list = []
        if merged_derived_data and "AOD" not in found_files:
            merged_derived_data = False
        found_files = found_files.split("\n")
        # print(found_files)
        for i in found_files:
            if merged_derived_data and "AOD" not in i:
                continue
            elif not merged_derived_data and "AOD" in i:
                continue
            file_list.append(i)
        # print(file_list)
        return file_list

    def local_file_position(self):
        return self.alien_path_analysis_results().replace("alien://", "")

    def get_run(self):
        return self.run_number

    def out_filename(self):
        if self.alien_path_analysis_results() is None:
            return None
        in_path = self.alien_path_analysis_results()
        file_name = path.basename(in_path)
        dir_name = path.dirname(in_path)
        target_output_file = path.join(self.out_path, dir_name.strip("/"), file_name)
        if self.merge_state == "partially_merged":
            if "Stage" not in target_output_file:
                fatal_msg("Cannot find Stage in", target_output_file)
            while "//" in target_output_file:
                target_output_file = target_output_file.replace("//", "/")
            target_output_file = target_output_file.split("Stage_")
            target_output_file = f"{target_output_file[0]}/AnalysisResults.root"
            # print(target_output_file)
        while "//" in target_output_file:
            target_output_file = target_output_file.replace("//", "/")
        return target_output_file

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
        if self.out_filename() is None:
            wmsg("Output filename is None, skipping download")
            return None
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
                f.write(f"Period{self.get_dataset_name()}\n")
                if self.merge_state != "done":
                    f.write(f"Merge state: {self.merge_state}\n")
        if not overwrite and self.exists():
            if self.is_sane():
                msg("File", f"`{self.out_filename()}`",
                    "already present, skipping for download")
                return self.out_filename()
            else:
                os.remove(self.out_filename())
                msg("File", self.out_filename(),
                    "was not sane, removing it and attempting second download", color=bcolors.BWARNING)

        msg("Downloading", self.get_alien_path(), "to", self.out_filename())
        cmd = f"alien_cp -q {self.get_alien_path()} file:{self.out_filename()}"
        run_cmd(cmd)
        if self.is_sane():
            return self.out_filename()
        else:
            wmsg("File", self.out_filename(), "is not sane after download")
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
        extra = None
        if not h:
            return None
        if h.GetEntries() <= 0:
            raise ValueError("Error", h.GetName(), "has no entries")
        if 0:
            can = draw_nice_canvas("before_fit", replace=False)
            h.Draw()
            can.Modified()
            can.Update()
            # input("Press enter to continue")
        projection_interval = None
        if "TH2" in h.ClassName():
            xrange = option["x_range"].split(", ")
            xrange = [float(i) for i in xrange]
            projection_interval = [h.GetYaxis().GetBinLowEdge(h.GetYaxis().FindBin(xrange[0])),
                                   h.GetYaxis().GetBinUpEdge(h.GetYaxis().FindBin(xrange[1])),
                                   h.GetYaxis().GetTitle()]
            extra = TNamed("projection_interval",
                           "Projection interval: " + f"{projection_interval[0]:.2f}, {projection_interval[1]:.2f}, {projection_interval[2]}")
            h = h.ProjectionX("tmp", h.GetYaxis().FindBin(xrange[0]), h.GetYaxis().FindBin(xrange[1]))
        fitrange = option["fit_range"].split(", ")
        fitrange = [float(i) for i in fitrange]
        fun = TF1(h.GetName()+"functionfit", option["function"], *fitrange)
        for i in enumerate(option["initial_parameters"].split(", ")):
            fun.SetParameter(i[0], float(i[1]))
            if f"par_range{i[0]}" in option:
                par_range = option[f"par_range{i[0]}"].split(", ")
                par_range = [float(i) for i in par_range]
                fun.SetParLimits(i[0], *par_range)
            # print(fun.GetParameter(i[0]))
        # fun.Print()
        # for strat in [3]:
        for strat in [0, 1, 2, 3]:
            ROOT.Math.MinimizerOptions().SetStrategy(strat)
            h.Fit(fun, option["fit_opt"], "", *fitrange)
        fit_converged = gMinuit and gMinuit.fCstatu and ("CONVERGED" in gMinuit.fCstatu or "OK" in gMinuit.fCstatu)
        if not fit_converged:
            # print("Fit in pT", "with strategy", strategy, "did not converge -> ", st)
            print("Fit did not converge", gMinuit, gMinuit.fCstatu)

        if (type(option["show_single_fit"]) is str and option["show_single_fit"] == "true") or (type(option["show_single_fit"]) is not str and option["show_single_fit"]):
            can = draw_nice_canvas("fit_canvas", replace=False)
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
        return fun.GetParameter(int(option["parameterindex"])), fun.GetParError(int(option["parameterindex"])), extra

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
        drawn_objects.append(obj)
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
            extra = None
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
            y, ye, extra = self.functionfit(name, option)
        else:
            raise ValueError(f"Quantity {quantity} not recognized")

        if ytitle is not None:
            h.GetYaxis().SetTitle(ytitle)
        h.SetBinContent(ib, y)
        h.SetBinError(ib, ye)
        if extra is not None:
            h.GetListOfFunctions().Add(extra)
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
            sub_file_list.append(HyperloopOutput(i, out_path=out_path, full_json=data))
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
                             cert_file="/tmp/tokencert_1000.pem",
                             list_derived_data=False):
    # Getting input for single
    l = get_run_per_run_files(train_id=hyperloop_train_id,
                              out_path=out_path,
                              list_merged_files=download_merged,
                              key_file=key_file,
                              cert_file=cert_file)
    if list_derived_data:
        total_list = []
        for i in l:
            total_list.append(i.find_derived_data())
        print(total_list)
        with open("/tmp/list_of_derived_data.txt", "w") as f:
            for i in total_list:
                for j in i:
                    f.write(f"alien://{j}\n")
        return ""

    downloaded = []
    if jobs > 1:
        with Pool() as pool:
            pool.map(download_file, l)
    for i in tqdm.tqdm(l, bar_format='{l_bar}{bar:10}{r_bar}{bar:-10b}'):
        d = i.copy_from_alien(overwrite=overwrite)
        if d is None:
            continue
        downloaded.append(d)
    print("Downloaded for ID", hyperloop_train_id, "=", downloaded)
    return " ".join(downloaded)


def main():
    global VERBOSE_MODE
    global DRY_MODE_RUNNING

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
                        help="Verbose mode")
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
    parser.add_argument("--list_derived_data", "-L", "--list_aods",
                        action="store_true",
                        help="List the derived data produced by an hyperloop train")
    args = parser.parse_args()
    if args.verbose:
        VERBOSE_MODE = True
        print("Turning on verbose mode")
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
                                                         cert_file=args.cert_file,
                                                         list_derived_data=args.list_derived_data))
    print("Files downloaded:")
    print(" ".join(files_downloaded))


if __name__ == "__main__":
    main()
