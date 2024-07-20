#!/usr/bin/env python3


"""
Script to trend variables run per run
"""

import download_hyperloop_per_run
from download_hyperloop_per_run import draw_label
from ROOT import TH1F, TGraph, TColor, TH1, TLegend, TGraphErrors
from utils import draw_nice_canvas
import argparse
import configparser
from run_numbers import *

trend_calls = -1
trend_objects = []


def main(hyperloop_train,
         input_configuration,
         draw_every_run=True,
         do_download=False,
         skip_non_sane_runs=True,
         label=""):
    global trend_calls
    trend_calls += 1
    parser = configparser.ConfigParser()
    parser.read(input_configuration)
    if do_download:
        download_hyperloop_per_run.process_one_hyperloop_id(hyperloop_train)
    l = download_hyperloop_per_run.get_run_per_run_files(train_id=hyperloop_train)
    for i in parser.sections():
        object_config = parser[i]
        trend = f"trend_{i}_{trend_calls}"
        trend = TH1F(trend, trend, len(l), 0, len(l))
        trend.SetBit(TH1.kNoStats)
        trend.SetBit(TH1.kNoTitle)
        graphs = {"skipped": TGraph(), "low": TGraph(), "high": TGraph()}
        graph_vs_rate = TGraphErrors()
        trend_objects.append(graph_vs_rate)
        graph_vs_rate.SetName("graph_vs_rate_" + i)
        graph_vs_rate.SetName("graph_vs_rate_")
        graph_vs_rate.GetXaxis().SetTitle("<INEL> (Hz) from ZDC")
        graph_vs_rate.SetMarkerStyle(20)
        graph_vs_rate_split = {}
        colors = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#ffff33', '#a65628', '#f781bf', '#999999']
        for j in l:
            if skip_non_sane_runs and not j.exists():
                print("Skipping", j, "something wrong with the file")
                bin_filled = j.fill_histo(trend, i, None)
                x = trend.GetXaxis().GetBinCenter(bin_filled)
                graphs["skipped"].AddPoint(x, 1)
                continue
            if not j.has_in_file(i):
                alt_name = "perf-k0s-resolution/K0sResolution/h2_masspT"
                j.get_as(alt_name, i)
            if draw_every_run:
                j.get(i)
                x_range = None
                y_range = None
                draw_opt = ""
                if "x_range" in object_config:
                    x_range = object_config["x_range"].split(", ")
                if "y_range" in object_config:
                    y_range = object_config["y_range"].split(", ")
                if "draw_opt" in object_config:
                    draw_opt = object_config["draw_opt"]
                if "x_range" in object_config:
                    j.draw(i, x_range=x_range, y_range=y_range, opt=draw_opt)
                input(f"Plotting run {j.get_run()} press enter to continue")
            j.fill_histo(trend, i, object_config["what_to_do"], object_config)
        # Computing average
        average = []
        run_counters = {}
        coordinates_vs_rate_per_run = {}
        for j in graphs:
            run_counters[j] = []
        for j in range(1, trend.GetNbinsX()+1):
            x = trend.GetXaxis().GetBinCenter(j)
            y = trend.GetBinContent(j)
            ye = trend.GetBinError(j)
            run_number = int(trend.GetXaxis().GetBinLabel(j))
            average.append(y)
            thr = float(object_config["maximum_threshold"])
            if y > thr:
                graphs["high"].AddPoint(x, thr)
                run_counters["high"].append(run_number)
            thr = float(object_config["minimum_threshold"])
            if y < thr:
                graphs["low"].AddPoint(x, thr)
                run_counters["low"].append(run_number)
            if run_number in rates:
                graph_vs_rate.AddPoint(rates[run_number], y)
                coordinates_vs_rate_per_run[run_number] = [rates[run_number], y]
                graph_vs_rate.SetPointError(graph_vs_rate.GetN()-1, 0, ye)
            else:
                graph_vs_rate.AddPoint(-run_number, y)
            for k in periods:
                if run_number in periods[k]:
                    if k not in graph_vs_rate_split:
                        col = TColor.GetColor(colors.pop(0))
                        graph_vs_rate_split[k] = TGraphErrors()
                        trend_objects.append(graph_vs_rate_split[k])
                        graph_vs_rate_split[k].SetMarkerStyle(20 + int(trend.GetName().split("_")[-1]))
                        graph_vs_rate_split[k].SetName(graph_vs_rate.GetName() + "_"+k)
                        graph_vs_rate_split[k].SetTitle(k)
                        graph_vs_rate_split[k].SetLineColor(col)
                        graph_vs_rate_split[k].SetMarkerColor(col)
                    print("Adding", run_number, rates[run_number], "to", k)
                    graph_vs_rate_split[k].AddPoint(rates[run_number], y)
                    graph_vs_rate_split[k].SetPointError(graph_vs_rate_split[k].GetN()-1, 0, ye)
                    break
        average = sum(average)/len(average)
        for j in range(graphs["skipped"].GetN()):
            graphs["skipped"].SetPoint(j, graphs["skipped"].GetPointX(j), average)
            run_counters["skipped"].append(j)
        can = draw_nice_canvas("trend" + i, extend_right=True, replace=False)
        extra_label = None
        if can.GetListOfPrimitives().GetEntries() == 0:
            if trend.GetListOfFunctions().GetEntries() > 0:
                extra_label = draw_label(trend.GetListOfFunctions()[0].GetTitle(), align=33, x=0.92, y=0.90)
        trend.Draw("same")
        trend_objects.append(trend)

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
        # draw_label(parser["dataset_name"])
        draw_label(label)

        can.Modified()
        can.Update()
        for j in run_counters:
            print(j, run_counters[j])
        can.SaveAs("/tmp/trend" + i.replace("/", "_") + ".png")
        if 1:
            graph_vs_rate.GetYaxis().SetTitle(trend.GetYaxis().GetTitle())
            can_vs_rate = draw_nice_canvas("trend_vs_rate" + i, extend_right=True, replace=False)
            if can_vs_rate.GetListOfPrimitives().GetEntries() == 0:
                graph_vs_rate.Draw("AP")
            else:
                graph_vs_rate.Draw("PSAME")
            leg = TLegend()
            for k in graph_vs_rate_split:
                graph_vs_rate_split[k].Draw("PESAME")
                leg.AddEntry(graph_vs_rate_split[k])
            leg.Draw()
            draw_label(label)
            for coord in coordinates_vs_rate_per_run:
                draw_label(f"{coord}",
                           coordinates_vs_rate_per_run[coord][0]*1.01,
                           coordinates_vs_rate_per_run[coord][1]*1.001,
                           align=11,
                           size=0.02,
                           ndc=False)
            if extra_label is not None:
                extra_label.Draw()
            can_vs_rate.Modified()
            can_vs_rate.Update()
            input("Press enter to continue (before save)")
            can_vs_rate.SaveAs("/tmp/trend_vs_rate" + i.replace("/", "_") + ".png")
            can_vs_rate.SaveAs("/tmp/trend_vs_rate" + i.replace("/", "_") + ".pdf")
    input("Press enter to continue")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("hyperloop_train_ids",
                        help="Train ID to consider",
                        nargs="+",
                        type=int)
    parser.add_argument("--input_configuration", "-i", "--ini",
                        help="Train ID to consider",
                        default="trendConfig/efficiency.ini")
    parser.add_argument("--download", "-d",
                        help="Download the output (to be ran on the first time only)",
                        action="store_true")
    parser.add_argument("--draw_every_run", "-D", "--single",
                        help="Download the output (to be ran on the first time only)",
                        action="store_true")
    parser.add_argument("--label", "-l",
                        help="Download the output (to be ran on the first time only)",
                        default="")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Increase verbosity")

    args = parser.parse_args()
    if args.verbose:
        download_hyperloop_per_run.set_verbose_mode()

    for i in args.hyperloop_train_ids:
        main(i,
             label=args.label,
             input_configuration=args.input_configuration,
             do_download=args.download,
             draw_every_run=args.draw_every_run)
