#!/usr/bin/env python3

"""
Script to download from the path of merged AnalysisResults the corresponding results for the single runs.
It can be used by providing the path on alien of the merged results.
Example usage: `./download_per_run.py TRAIN_ID`
"""

import os
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

from utils import draw_nice_canvas, draw_nice_frame

# Modes
VERBOSE_MODE = False


def set_verbose_mode():
    global VERBOSE_MODE
    VERBOSE_MODE = True
    print("Turning on verbose mode")


DRY_MODE_RUNNING = False


def set_dry_mode():
    global DRY_MODE_RUNNING
    DRY_MODE_RUNNING = True
    print("Turning on dry mode")


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
    import subprocess
    import inspect
    if "capture_output" in inspect.signature(subprocess.run).parameters:
        # Python 3.7+
        run_result = subprocess.run(cmd, capture_output=True)
    else:
        run_result = subprocess.run(cmd)
    if print_output:
        if run_result.stdout is not None:
            vmsg("-- stdout:", run_result.stdout.decode('ascii'))
        if run_result.stderr is not None and run_result.stderr != b"":
            vmsg("-- stderr:", run_result.stderr.decode('ascii'))
    return run_result


drawn_objects = []


class HyperloopOutput:
    def __init__(self,
                 json_entry,
                 full_json=None,
                 out_path="/tmp/"):

        self.out_path = os.path.abspath(out_path)

        def get(key):
            # Gets the key from the json entry
            if key in json_entry:
                return json_entry[key]
            return None

        def getgeneral(key):
            # Gets the key from the general json entry
            if full_json is None:
                return None
            if key in full_json:
                return full_json[key]
            return None

        self.alien_outputdir = get("outputdir")
        self.run_number = get("run")
        vmsg("Adding hyperloop output for run number", self.run_number)
        self.merge_state = get("merge_state")
        self.derived_data = get("derived_data")
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
        if self.derived_data is None:
            return None
        # Check if it is already there
        out_name = os.path.join(self.out_path, f"HyperloopID_{self.run_number}.json")

        if os.path.isfile(self.local_file_position()):
            print("YOOO")

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
        file_name = os.path.basename(in_path)
        dir_name = os.path.dirname(in_path)
        target_output_file = os.path.join(self.out_path, dir_name.strip("/"), file_name)
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
        check = os.path.isfile(f)
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
        # Check that the size is the same
        alien_size = self.get_alien_file_size()
        local_size = os.path.getsize(f)
        if abs(alien_size - local_size) > 1000:
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

    def get_alien_file_size(self):
        cmd = f"alien_stat {self.get_alien_path()}"
        out = run_cmd(cmd)
        out = out.stdout.decode('ascii')
        s = None
        for i in out.split("\n"):
            if "Size" in i:
                s = int(i.split(" ")[1])
                break
        if s is None:
            wmsg("Cannot find size in", out)
            return 0
        return s
        print("Size", s, "bytes", s/1024/1024/1024, "GB")
        raise ValueError("Not implemented")

    def copy_from_alien(self,
                        write_download_summary=True,
                        overwrite=False,
                        overwrite_summary=True):
        if self.out_filename() is None:
            wmsg("Output filename is None, skipping download")
            return None
        out_path = os.path.dirname(self.out_filename())
        if not os.path.isdir(out_path):
            vmsg("Preparing directory", f"`{out_path}`")
            os.makedirs(out_path)
        else:
            vmsg("Directory", f"`{out_path}`", "already present")
        if write_download_summary and (overwrite_summary or not os.path.isfile(os.path.join(out_path, "download_summary.txt"))):
            with open(os.path.join(out_path, "download_summary.txt"), "w") as f:
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

    def copy_from_alien_derived_data(self,
                                     write_download_summary=True,
                                     overwrite=False,
                                     overwrite_summary=True):
        list_of_derived_data = self.find_derived_data()

        if self.out_filename() is None:
            wmsg("Output filename is None, skipping download")
            return None
        out_path = os.path.dirname(self.out_filename())
        if not os.path.isdir(out_path):
            vmsg("Preparing directory", f"`{out_path}`")
            os.makedirs(out_path)
        else:
            vmsg("Directory", f"`{out_path}`", "already present")
        if write_download_summary and (overwrite_summary or not os.path.isfile(os.path.join(out_path, "download_summary.txt"))):
            with open(os.path.join(out_path, "download_summary.txt"), "w") as f:
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

    def has_in_file(self, name):
        if self.open().Get(name):
            return True
        return False

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
                    if "/" in name:
                        split_names = name.split("/")
                        partial_name = split_names.pop(0)
                        print(f"Looking for content in {partial_name}")
                        f.Get(partial_name).ls()
                        for j in split_names:
                            partial_name += f"/{j}"
                            print(f"Looking for {partial_name}")
                            f.Get(partial_name).ls()
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

    def get_as(self, name, alias):
        if alias in self.root_objects:
            return self.root_objects[alias]
        self.root_objects[alias] = self.get(name)
        return self.get(alias)

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
            projection_range = option["projection_range"].split(", ")
            if len(projection_range) != 2:
                raise ValueError("projection_range not properly set")
            projection_range = [float(i) for i in projection_range]
            projection_interval = [h.GetYaxis().GetBinLowEdge(h.GetYaxis().FindBin(projection_range[0])),
                                   h.GetYaxis().GetBinUpEdge(h.GetYaxis().FindBin(projection_range[1])),
                                   h.GetYaxis().GetTitle()]
            extra = TNamed("projection_interval",
                           "Projection interval: " + f"{projection_interval[0]:.2f}, {projection_interval[1]:.2f}, {projection_interval[2]}")
            if option["projection"] == "x":
                h = h.ProjectionX("tmp", h.GetYaxis().FindBin(projection_range[0]), h.GetYaxis().FindBin(projection_range[1]))
            elif option["projection"] == "y":
                h = h.ProjectionY("tmp", h.GetXaxis().FindBin(projection_range[0]), h.GetXaxis().FindBin(projection_range[1]))
            if 0:  # Show projection
                can = draw_nice_canvas("projection", replace=False)
                h.Draw()
                can.Modified()
                can.Update()
                input("Press enter to continue")

        fitrange = option["fit_range"].split(", ")
        if len(fitrange) != 2:
            raise ValueError("fit_range not properly set")

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
        h.Fit(fun, "QNR")
        if 0:
            fun.Draw("SAME")
            input("Press enter to continue")

        if 0:
            for strat in [0, 1, 2, 3]:
                ROOT.Math.MinimizerOptions().SetStrategy(strat)
                h.Fit(fun, option["fit_opt"], "", *fitrange)
            fit_converged = gMinuit and gMinuit.fCstatu and ("CONVERGED" in gMinuit.fCstatu or "OK" in gMinuit.fCstatu)
            if not fit_converged:
                if gMinuit:
                    status = gMinuit and gMinuit.fCstatu
                else:
                    status = "No gMinuit"
                wmsg("Fit did not converge", status, "with strategy", strat)

        show_single_fit = option["show_single_fit"]
        if (type(show_single_fit) is str and show_single_fit == "true") or (type(show_single_fit) is not str and show_single_fit):
            can = draw_nice_canvas("fit_canvas", replace=False)
            h.SetBit(TH1.kNoStats)
            h.SetBit(TH1.kNoTitle)
            show_single_fit_range = option["show_single_fit_range"]
            if show_single_fit_range is not None:
                show_single_fit_range = show_single_fit_range.split(", ")
                show_single_fit_range = [float(i) for i in show_single_fit_range]
                h.GetXaxis().SetRangeUser(show_single_fit_range[0], show_single_fit_range[1])
            h.Draw()
            fun.Draw("same")
            if projection_interval is not None:
                draw_label("Projection interval: " + f"{projection_interval[0]:.2f}, {projection_interval[1]:.2f}, {projection_interval[2]}")
            draw_label(h.GetTitle(), 0.77, 0.85)
            draw_label(f"Run {self.get_run()}", 0.25, 0.85)
            can.Modified()
            can.Update()
            input("Press enter to continue")
        parameter_index = int(option["parameterindex"])
        print("Getting the input parameter", parameter_index, fun.GetParName(parameter_index))
        return fun.GetParameter(parameter_index), fun.GetParError(parameter_index), extra

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
            obj.SetDirectory(0)
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
        vmsg("Drawn", name, "for run", self.get_run(), "x_range", x_range, "y_range", y_range)
        return can

    def fill_histo(self, h_trending, name, quantity="mean", option=None):
        """
        This function fills the histogram h_trending with the quantity specified of the object asked.
        """
        x = f"{self.get_run()}"
        ib = int(h_trending.GetEntries()) + 1
        if h_trending.GetXaxis().GetTitle() == "":
            h_trending.SetBit(TH1.kNoStats)
            h_trending.GetXaxis().SetTitle("Run number")
        ytitle = None
        if h_trending.GetYaxis().GetTitle() == "" and quantity is not None:
            ytitle = self.get(name).GetTitle()
        h_trending.GetXaxis().SetBinLabel(ib, x)
        extra = None
        y = 0
        ye = 0
        if quantity is None:
            y = 0
            ye = 0
            ytitle = "None"
        elif quantity == "mean":
            if ytitle is not None:
                ytitle = f"<{ytitle}>"
            y, ye = self.average(name)
        elif quantity == "valueat1":
            if ytitle is not None:
                ytitle = f"Value at 1" + h_trending.GetXaxis().GetTitle()
            y, ye = self.valueat1(name)
        elif quantity == "functionfit":
            if ytitle is not None:
                ytitle = option["treding_title"].strip("\"")
            y, ye, extra = self.functionfit(name, option)
        else:
            raise ValueError(f"Quantity {quantity} not recognized")

        if ytitle is not None:
            h_trending.GetYaxis().SetTitle(ytitle)
        h_trending.SetBinContent(ib, y)
        h_trending.SetBinError(ib, ye)
        if extra is not None:
            h_trending.GetListOfFunctions().Add(extra)
        return ib

    def __lt__(self, other):
        return self.run_number < other.run_number


def get_run_per_run_files(train_id=126264,
                          alien_path="https://alimonitor.cern.ch/alihyperloop-data/trains/train.jsp?train_id=",
                          out_path="/tmp/",
                          list_merged_files=False,
                          key_file="/tmp/tokenkey_1000.pem",
                          cert_file="/tmp/tokencert_1000.pem"):
    out_name = os.path.join(out_path, f"HyperloopID_{train_id}.json")
    if not os.path.isfile(key_file):
        fatal_msg("Cannot find key file", key_file)
    if not os.path.isfile(cert_file):
        fatal_msg("Cannot find cert file", cert_file)
    if not os.path.isfile(out_name):
        download_cmd = f"curl --key {key_file} --cert {cert_file} --insecure {alien_path}{train_id} -o {out_name}"
        run_cmd(download_cmd)
    sub_file_list = []
    with open(out_name) as json_data:
        import json
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


def download_derived_data(i):
    return i.copy_from_alien_derived_data(overwrite=False)


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
    list_of_hl_output = get_run_per_run_files(train_id=hyperloop_train_id,
                                              out_path=out_path,
                                              list_merged_files=download_merged,
                                              key_file=key_file,
                                              cert_file=cert_file)
    if list_derived_data:
        total_list = []
        for i in list_of_hl_output:
            print(i)
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
            pool.map(download_file, list_of_hl_output)
    for i in tqdm.tqdm(list_of_hl_output, bar_format='{l_bar}{bar:10}{r_bar}{bar:-10b}'):
        d = i.copy_from_alien(overwrite=overwrite)
        if d is None:
            continue
        downloaded.append(d)
    print("Downloaded for ID", hyperloop_train_id, "=", downloaded)
    return " ".join(downloaded)


def main():
    global VERBOSE_MODE
    global DRY_MODE_RUNNING

    import argparse
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
        set_verbose_mode()
    if args.drymode:
        set_dry_mode()

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
