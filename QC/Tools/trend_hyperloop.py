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

rates = {}

rates[544013] = 6278.43
rates[544028] = 30336.7
rates[544032] = 23718.5
rates[544033] = 4957.46
rates[544091] = 29326.7
rates[544095] = 25101.8
rates[544098] = 18005.6
rates[544116] = 38342
rates[544121] = 22543.5
rates[544122] = 16559.5
rates[544123] = 11629.7
rates[544124] = 6610.2
rates[544126] = 51.437
rates[544167] = 45633.8
rates[544180] = 45755.2
rates[544184] = 32927.3
rates[544185] = 28727.2
rates[544384] = 41927
rates[544389] = 26876.1
rates[544390] = 17959.1
rates[544391] = 14724.2
rates[544392] = 12663.5

rates[544418] = 10200.2
rates[544420] = 5373.17
rates[544434] = 4385.37
rates[544451] = 27927.2
rates[544454] = 19440.6
rates[544474] = 29367.4
rates[544475] = 19438.5
rates[544476] = 16104.7
rates[544477] = 13211.6
rates[544490] = 43111.7
rates[544491] = 24276.6
rates[544492] = 15135.7
rates[544508] = 39628
rates[544510] = 29528.7
rates[544511] = 21593.6
rates[544512] = 18389.5
rates[544513] = 16239.1
rates[544514] = 15066
rates[544515] = 13300.4
rates[544516] = 12546.1
rates[544518] = 10720.7

periods = {}
periods["LHC23zzf_apass1"] = [544013]
periods["LHC23zzg_apass1"] = [544028, 544032]
periods["LHC23zzh_apass1"] = [544091, 544095, 544098]
periods["LHC23zzi_apass1"] = [544167, 544180, 544184, 544185, 544389, 544390, 544391, 544392]
periods["LHC23zzk_apass1"] = [544451, 544454, 544474, 544475, 544476, 544477, 544490, 544491, 544492, 544508, 544510]


def main(hyperloop_train,
         input_configuration,
         draw_every_run=True,
         do_download=False,
         skip_non_sane_runs=True,
         label="LHC23_PbPb_pass1_sampling"):
    parser = configparser.ConfigParser()
    parser.read(input_configuration)
    if do_download:
        download_hyperloop_per_run.main(hyperloop_train)
    l = download_hyperloop_per_run.get_run_per_run_files(train_id=hyperloop_train)
    for i in parser.sections():
        object_config = parser[i]
        trend = TH1F("trend"+i, "trend"+i, len(l), 0, len(l))
        trend.SetBit(TH1.kNoStats)
        trend.SetBit(TH1.kNoTitle)
        graphs = {"skipped": TGraph(), "low": TGraph(), "high": TGraph()}
        graph_vs_rate = TGraphErrors()
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
                input(f"Run {j.get_run()}\nPress enter to continue")
            j.fill_histo(trend, i, object_config["what_to_do"], object_config)
        # Computing average
        average = []
        run_counters = {}
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
                graph_vs_rate.SetPointError(graph_vs_rate.GetN()-1, 0, ye)
            else:
                graph_vs_rate.AddPoint(-run_number, y)
            for k in periods:
                if run_number in periods[k]:
                    if k not in graph_vs_rate_split:
                        col = TColor.GetColor(colors.pop(0))
                        graph_vs_rate_split[k] = TGraphErrors()
                        graph_vs_rate_split[k].SetMarkerStyle(20)
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
        can = draw_nice_canvas("trend" + i, extend_right=True)
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
        # draw_label(parser["dataset_name"])
        draw_label(label)

        can.Modified()
        can.Update()
        for j in run_counters:
            print(j, run_counters[j])
        can.SaveAs("/tmp/trend" + i.replace("/", "_") + ".png")
        if 1:
            graph_vs_rate.GetYaxis().SetTitle(trend.GetYaxis().GetTitle())
            draw_nice_canvas("trend_vs_rate" + i, extend_right=True)
            graph_vs_rate.Draw("AP")
            leg = TLegend()
            for k in graph_vs_rate_split:
                graph_vs_rate_split[k].Draw("PESAME")
                leg.AddEntry(graph_vs_rate_split[k])
            leg.Draw()
            draw_label(label)
    input("Press enter to continue")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("hyperloop_train_id",
                        help="Train ID to consider",
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

    args = parser.parse_args()
    main(args.hyperloop_train_id,
         input_configuration=args.input_configuration,
         do_download=args.download,
         draw_every_run=args.draw_every_run)
