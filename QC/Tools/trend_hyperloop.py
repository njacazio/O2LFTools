#!/usr/bin/env python3


"""
Script to trend variables run per run
"""

import download_hyperloop_per_run
from ROOT import TH1F, TCanvas, TGraph, TColor
import argparse
import configparser


def main(hyperloop_train,
         input_configuration,
         draw_every_run=True,
         do_download=False,
         skip_non_sane_runs=True):
    parser = configparser.ConfigParser()
    parser.read(input_configuration)
    if do_download:
        download_hyperloop_per_run.main(hyperloop_train)
    l = download_hyperloop_per_run.get_run_per_run_files(train_id=hyperloop_train)
    for i in parser.sections():
        object_config = parser[i]
        trend = TH1F("trend"+i, "trend"+i, len(l), 0, len(l))
        graphs = {"skipped": TGraph(), "low": TGraph(), "high": TGraph()}
        for j in l:
            if skip_non_sane_runs and not j.exists():
                print("Skipping", j, "something wrong with the file")
                bin_filled = j.fill_histo(trend, i, None)
                x = trend.GetXaxis().GetBinCenter(bin_filled)
                graphs["skipped"].AddPoint(x, 1)
                continue
            if draw_every_run:
                j.get(i)
                if "x_range" in object_config:
                    j.draw(i, x_range=object_config["x_range"].split(", "),
                           y_range=object_config["y_range"].split(", "))
                else:
                    j.draw(i)
                input(f"Run {j.get_run()}\nPress enter to continue")
            j.fill_histo(trend, i, object_config["what_to_do"])
        # Computing average
        average = []
        run_counters = {}
        for j in graphs:
            run_counters[j] = []
        for j in range(1, trend.GetNbinsX()+1):
            x = trend.GetXaxis().GetBinCenter(j)
            y = trend.GetBinContent(j)
            r = int(trend.GetXaxis().GetBinLabel(j))
            average.append(y)
            thr = float(object_config["maximum_threshold"])
            if y > thr:
                graphs["high"].AddPoint(x, thr)
                run_counters["high"].append(r)
            thr = float(object_config["minimum_threshold"])
            if y < thr:
                graphs["low"].AddPoint(x, thr)
                run_counters["low"].append(r)
        average = sum(average)/len(average)
        for j in range(graphs["skipped"].GetN()):
            graphs["skipped"].SetPoint(j, graphs["skipped"].GetPointX(j), average)
            run_counters["skipped"].append(r)
        can = TCanvas("trend" + i)
        can.Draw()
        trend.Draw()
        colours = {"skipped": "#e41a1c", "low": "#377eb8", "high": "#4daf4a"}
        markers = {"skipped": 4, "low": 22, "high": 23}
        for j in graphs:
            g = graphs[j]
            if g.GetN() == 0:
                continue
            g.SetTitle(j)
            g.SetMarkerStyle(markers[j])
            col = TColor.GetColor(colours[j])
            g.SetMarkerColor(col)
            g.Draw("PSAME")
        can.Modified()
        can.Update()
        for j in run_counters:
            print(j, run_counters[j])
    input("Press enter to continue")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("hyperloop_train_id",
                        help="Train ID to consider",
                        type=int)
    parser.add_argument("--input_configuration", "-i",
                        help="Train ID to consider",
                        default="trendConfig/efficiency.ini")
    args = parser.parse_args()
    main(args.hyperloop_train_id,
         input_configuration=args.input_configuration)
