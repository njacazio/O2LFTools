#!/usr/bin/env python3

import os
from ROOT import TGraph, TDatime, TColor, TLegend
from utils import draw_nice_canvas, draw_nice_frame
import subprocess
import argparse


def run_cmd(cmd, verbose=False):
    process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    if verbose:
        # print(cmd)
        print(output.decode())
    return output


def main(path_to_o2physics, last_modified=False, check_if_datamodel=False, show_authors=False, check_if_produces_table=False):
    lp = os.path.join(os.path.normpath(os.path.expanduser(path_to_o2physics)), "O2Physics/PWGLF")
    os.chdir(lp)
    list_of_files = {}
    available_dirs = []
    never_updated = 0
    for i in os.listdir(lp):
        p = os.path.join(lp, i)
        if not os.path.isdir(p):
            continue
        if i not in available_dirs:
            available_dirs.append(i)
        for j in os.listdir(p):
            filetag = os.path.join(p, j)
            if not os.path.isfile(filetag):
                continue
            if "CMakeLists.txt" in filetag:
                continue
            if check_if_datamodel or check_if_produces_table:
                has_it = False
                with open(filetag, "r") as f:
                    for l in f:
                        if check_if_datamodel:
                            if "DECLARE_SOA_TABLE" in l:
                                has_it = True
                                break
                        if check_if_produces_table:
                            if "Produces<" in l:
                                has_it = True
                                break
                if not has_it:
                    continue
            # print(filetag)
            if 0:
                run_cmd("pwd", True)
            cmd = f"git log --format=\"format:%ci\" --name-only --diff-filter=A {os.path.join(i, j)}"
            if last_modified:
                cmd = f"git log --format=\"format:%ci\" --name-only --diff-filter=M {os.path.join(i, j)}"
            # print(cmd)
            output = run_cmd(cmd)
            # print(output)
            formatted_output = output.decode().split("\n")
            formatted_output = [l for l in formatted_output if "format:" in l]
            formatted_output = [l.replace("format:", "").strip("\"") for l in formatted_output]
            formatted_output = [l.split(" ")[0] for l in formatted_output]
            # print(formatted_output)
            if len(formatted_output) == 0:
                print(filetag.replace(os.path.expanduser(path_to_o2physics), ""),
                      "was never updated, added on",
                      run_cmd(f"git log --format=%ci --name-only --diff-filter=A {os.path.join(i, j)}").decode().split("\n")[0].strip().split(" ")[0])
                never_updated += 1
                continue
            formatted_output = formatted_output[0]
            list_of_files[filetag] = formatted_output
            # print(formatted_output)
    print("Available directories", available_dirs)
    if never_updated > 0:
        print("Found", never_updated, "files that were never updated")
    if check_if_datamodel:
        print("Found", len(list_of_files), "total files that declare a data model")
    else:
        print("Found", len(list_of_files), "total files")

    graphs = {}

    def make_graph(req=None):
        # First we order per time
        time_ordered = {}
        for i in list_of_files:
            t = list_of_files[i]
            # print(t)
            if req is not None and req not in i:
                continue
            if t not in time_ordered:
                print("Adding new time", t)
                time_ordered[t] = []
            time_ordered[t].append(i)
        #     print(t)
        # print(time_ordered)

        g = TGraph()
        g.SetLineWidth(2)
        g.SetMarkerStyle(20)
        graphs[req] = g
        tit = "All"
        if req is not None:
            tit = req

        colors = {'TableProducer': '#e41a1c', 'Tasks': '#377eb8', 'DataModel': '#4daf4a', 'Utils': '#984ea3'}
        if req in colors:
            col = TColor.GetColor(colors[req])
            g.SetLineColor(col)
            g.SetMarkerColor(col)
        g.SetTitle(tit)
        g.GetYaxis().SetTitle("Number of files")
        g.GetXaxis().SetTimeDisplay(1)
        g.GetXaxis().SetNdivisions(-503)
        g.GetXaxis().SetTimeFormat("%Y-%m-%d %H:%M")
        g.GetXaxis().SetTimeOffset(0, "gmt")
        sorted_t = list(time_ordered.keys())
        sorted_t.sort()

        found = []
        for i in sorted_t:
            t = i.split("-")
            if len(t) != 3:
                raise ValueError(i, "cannot be split into time")
            # print(t)
            y = int(t[0])
            m = int(t[1])
            d = int(t[2])
            found += time_ordered[i]
            if last_modified:
                g.SetPoint(g.GetN(), TDatime(y, m, d, 00, 00, 00).Convert(), len(time_ordered[i]))
            else:
                g.SetPoint(g.GetN(), TDatime(y, m, d, 00, 00, 00).Convert(), len(found))
        print("Found", len(found), "in", req)
        for i in found:
            print("\t", i.replace(os.path.expanduser(path_to_o2physics), ""))
            if show_authors:
                run_cmd(f"git shortlog -n -s -- {i}", True)

        if req is not None:
            for i in found:
                print("\t", i)
        if len(found) == 0:
            g.SetPoint(0, -1, -1)
        return g

    can = draw_nice_canvas("all")
    gall = make_graph()
    xtitle = "Time of first addition"
    if last_modified:
        xtitle = "Time of last update"
    ytitle = "Number of files"
    if check_if_datamodel:
        ytitle = "Number of files with DECLARE_SOA_TABLE"
    if check_if_produces_table:
        ytitle = "Number of files that produce table"
    frame = draw_nice_frame(can,
                            [gall.GetPointX(0)-3600*24*30, gall.GetPointX(gall.GetN()-1)+3600*24*30],
                            [0, max(gall.GetY())*1.2 + 1],
                            xt=xtitle,
                            yt=ytitle)
    frame.GetXaxis().SetTimeDisplay(1)
    frame.GetXaxis().SetNdivisions(-503)
    frame.GetXaxis().SetTimeFormat("%Y-%m-%d")
    frame.GetXaxis().SetTimeOffset(0, "gmt")

    gall.Draw("LPsame")
    for i in available_dirs:
        make_graph(i).Draw("LPsame")
    leg = TLegend(0.2, .7, 0.4, 0.9)
    for i in graphs:
        if graphs[i].GetPointX(0) <= 0:
            continue
        leg.AddEntry(graphs[i])

    leg.Draw()
    can.Update()

    input("Press enter to continue")


if __name__ == "__main__":
    paser = argparse.ArgumentParser()
    paser.add_argument("o2physics_path", help="Path to O2Physics")
    paser.add_argument("--last_modified", action="store_true", help="Last modified instead of first added")
    paser.add_argument("--check_if_datamodel", action="store_true", help="Check if there is a DECLARE_SOA_TABLE")
    paser.add_argument("--check_if_produces", action="store_true", help="Check if a file produces a table")
    args = paser.parse_args()
    main(path_to_o2physics=args.o2physics_path, last_modified=args.last_modified, check_if_datamodel=args.check_if_datamodel, check_if_produces_table=args.check_if_produces)
