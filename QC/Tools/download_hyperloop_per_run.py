#!/usr/bin/env python3

"""
Script to download from the path of merged AnalysisResults the corresponding results for the single runs.
It can be used by providing the path on alien of the merged results.
Example usage: `./download_per_run.py /alice/cern.ch/user/a/alihyperloop/outputs/38641/4474`
"""

import subprocess
from os import path
try:
    from bs4 import BeautifulSoup
except:
    raise Exception(
        "Cannot find bs4, consider running `pip3 install --user beautifulsoup4`")
try:
    import lxml
except:
    raise Exception(
        "Cannot find lxml, consider running `pip3 install --user lxml`")
import os
import argparse
try:
    from ROOT import TFile
except:
    raise Exception("Cannot find ROOT, are you in a ROOT enviroment?")

try:
    import tqdm
except ImportError as e:
    print("Module tqdm is not imported.",
          "Progress bar will not be available (you can install tqdm for the progress bar) `pip3 install --user tqdm`")

import sys
import inspect

# Modes
verbose_mode = False
dry_mode = False


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
    if verbose_mode:
        print("** ", color, *args, bcolors.ENDC)


def msg(*args, color=bcolors.BOKBLUE):
    print(color, *args, bcolors.ENDC)


def fatal_msg(*args, fatal_message="Fatal Error!"):
    msg("[FATAL]", *args, color=bcolors.BFAIL)
    raise RuntimeError(fatal_message)


def copy_from_alien(in_path,
                    file_name,
                    out_path,
                    preserve_structure=False,
                    overwrite=False,
                    tag=None):
    in_path = in_path.replace("alien://", "")
    out_path = path.abspath(out_path)
    if file_name is None:
        file_name = path.basename(in_path)
        in_path = path.dirname(in_path)
    if preserve_structure:
        vmsg("Preserving path structure in download")
        out_path = path.join(out_path, in_path.strip("/"))
        if not path.isdir(out_path):
            vmsg("Preparing directory", f"`{out_path}`")
            os.makedirs(out_path)
    out_file = path.join(out_path, file_name)
    if tag is not None:
        tag = tag.strip()
        if tag == "":
            fatal_msg("Emtpy tag, nothing to do.")
        if not tag.startswith("_"):
            tag = f"_{tag}"
        new_name = [path.dirname(file_name),
                    path.basename(file_name)]
        new_name[1] = f"{tag}.".join(new_name[1].rsplit(".", 1))
        new_name = path.join(*new_name)
        msg("Tagging", file_name, "with tag", tag, "to", new_name)
        out_file = path.join(out_path, new_name)

    if path.isfile(out_file):
        if not overwrite:
            if check_sanity(out_file, throw_fatal=False):
                msg("File", f"`{out_file}`",
                    "already present, skipping for download")
                return out_file
            else:
                os.remove(out_file)
                msg("File", out_file, "was not sane, removing it and attempting second download", color=bcolors.BWARNING)

        else:
            n = 0
            new_name = file_name.rsplit('.', 1)
            for revision in os.listdir(out_path):
                if revision.startswith(new_name[0]):
                    n += 1
            new_name = f"_Rev{n}.".join(new_name)
            new_name = out_file.replace(file_name, new_name)
            os.rename(out_file, new_name)
            msg("File", f"`{out_file}`",
                "already present, renaming it to", new_name)
    full_path = path.join(in_path, file_name)
    msg("Downloading", full_path)
    cmd = f"alien_cp -q alien://{full_path} file:{out_file}"
    vmsg("Running:", f"`{cmd}`")
    if not dry_mode:
        cmd = cmd.split()
        if "capture_output" in inspect.signature(subprocess.run).parameters:
            # Python 3.7+
            run_result = subprocess.run(cmd, capture_output=not verbose_mode)
        else:
            run_result = subprocess.run(cmd)
    return out_file


def check_sanity(file_name, throw_fatal=True):
    try:
        f = TFile.Open(file_name)
    except:
        if throw_fatal:
            fatal_msg("Cannot open", file_name)
        return False
    return True


def get_run_per_run_files(alien_path="/alice/cern.ch/user/a/alihyperloop/outputs/35071/4143",
                          xml_name="Stage_1.xml",
                          out_path="/tmp/"):
    overwrite_xml = True
    if path.isfile(path.join(out_path, xml_name)):
        with open(path.join(out_path, xml_name)) as f:
            for i in f:
                if alien_path in i:
                    overwrite_xml = False
                    break

    copy_from_alien(alien_path, xml_name, out_path, overwrite=overwrite_xml)

    with open(path.join(out_path, xml_name), "r") as f:
        data = f.read()
    Bs_data = BeautifulSoup(data, "xml")
    b_file = Bs_data.find_all('file')
    sub_file_list = []
    for i in b_file:
        sub = i.get("turl")
        vmsg("Add", f"`{sub}`", "to the list of files to download")
        sub_file_list.append(sub)
    msg("Found", len(sub_file_list), "files to download")
    return sub_file_list


def main(merged_output_alien_path="/alice/cern.ch/user/a/alihyperloop/outputs/35071/4143",
         out_path="/tmp/",
         overwrite=False,
         organize_based_on_run_number=False,
         tag=None,
         no_explicit_pass=False,
         download_merged=False):
    # Getting input for merged file
    l = get_run_per_run_files(alien_path=merged_output_alien_path,
                              out_path=out_path)
    
    # Downloading files run per run
    def do_download(full_path):
        return copy_from_alien(full_path,
                               file_name=None,
                               out_path=out_path,
                               preserve_structure=True,
                               overwrite=overwrite,
                               tag=tag)
    downloaded = []

    if organize_based_on_run_number:
        print("\n!!! BEWARE: be sure that the package \"tdqm\" is loaded!\n")

    if "tqdm" in sys.modules:
        for i in tqdm.tqdm(l, bar_format='{l_bar}{bar:10}{r_bar}{bar:-10b}'):
            downloaded.append(do_download(i))
            if organize_based_on_run_number:
                do_download("/".join(i.split("/")[:-1])+"/analysis.xml")
    else:
        for i in l:
            downloaded.append(do_download(i))

    # Download merged output file
    if download_merged:
        merged = merged_output_alien_path + "/AnalysisResults.root"
        msg("\nDownloading merged output ", merged)
        copy_from_alien(in_path=merged, file_name=None, out_path=out_path)
        merged = out_path + "AnalysisResults.root"
        cmd = f"mv {merged} {out_path}/AnalysisResults_full_stat.root"
        vmsg("Running:", f"`{cmd}`")
        cmd = cmd.split()
        if "capture_output" in inspect.signature(subprocess.run).parameters:
            # Python 3.7+
            run_result = subprocess.run(cmd, capture_output=not verbose_mode)
        else:
            run_result = subprocess.run(cmd)

    # Checking
    for i in downloaded:
        check_sanity(i)
    msg("You can find the", len(downloaded), "downloaded files in", out_path)
    for i in downloaded:
        msg("        ", i)
    if organize_based_on_run_number:
        msg("Organizing files based on run number")
        linked = []
        for d in downloaded:
            anaxml = "/".join(d.split("/")[:-1])+"/analysis.xml"
            with open(path.join(out_path, anaxml), "r") as f:
                data = f.read()
                Bs_data = BeautifulSoup(data, "xml")
                for i in Bs_data.find_all('file'):
                    i = i.get("turl")
                    i = i.replace("alien:///", "")
                    apassindex = -1
                    for j in enumerate(i.split("/")):
                        if "apass" in j[1]:
                            apassindex = j[0]
                            break
                        if "cpass" in j[1]:
                            apassindex = j[0]
                            break
                    if no_explicit_pass:
                        msg("BEWARE: no explicit apass/cpass in the output paths")
                    else:
                        if apassindex < 0:
                            fatal_msg("Try option -np: cannot find apass/cpass in", i)
                        i = "/".join(i.split("/")[:apassindex+1])
                    i = os.path.join(out_path, "run_organized", i)
                    if not os.path.isdir(i):
                        msg("Making directory", i)
                        os.makedirs(i)
                    target = os.path.join(i, os.path.basename(d))
                    linked.append(target)
                    if os.path.isfile(target):
                        break
                    msg("Linking", d, "to", target)
                    os.link(d, target)
                    break
                # b_file = Bs_data.find_all('file')
        return linked


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_path", help="Input path to look for in grid. One can use e.g. `/alice/cern.ch/user/a/alihyperloop/outputs/38641/4474`. This path can be found e.g. in https://alimonitor.cern.ch/hyperloop/train-run/38641 under the tab `Merged Output`. It is the path of the merged analysis results")
    parser.add_argument("--out_path", "-o",
                        default="/tmp/",
                        help="Output path where the download will be located. Default: `/tmp/`")
    parser.add_argument("--xml_file", "-x",
                        default="Stage_1.xml",
                        help="Name of the file used for merge. Default: `Stage_1.xml`")
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
    parser.add_argument("--look_for_run_number", "-r",
                        action="store_true",
                        help="Flag to look for the run number of the downloaded files and rename the path accordingly. Default: `False`")
    parser.add_argument("--no_pass", "-np",
                        action="store_true",
                        help="Flag to disable the research of apass/cpass in the Hyperloop output files. Default: `False`")
    parser.add_argument("--download_merged", "-m",
                        action="store_true",
                        help="Flag to enable the download of the merged output file. Default: `False`")
    args = parser.parse_args()
    if args.verbose:
        verbose_mode = True
    if args.drymode:
        dry_mode = True
    main(merged_output_alien_path=args.input_path,
         out_path=args.out_path,
         overwrite=args.overwrite,
         organize_based_on_run_number=args.look_for_run_number,
         tag=args.tag,
         no_explicit_pass=args.no_pass,
         download_merged=args.download_merged)
