#!/usr/bin/env python3

from ROOT import gMinuit, TFile, TGraphErrors, TF1, TColor, TLegend
import ROOT

import os
from sys import argv
import sys
if 1:
    sys.path.append('../../PerformancePlots/')
    from utils import draw_nice_canvas, draw_nice_frame, draw_nice_label, getfromfile, update_all_canvases, make_color_range


def process_one_file(filename,
                     charge="Pos",
                     tag_it=True):
    h = getfromfile(filename, "qa-impact-par/Reco/h4ImpPar")
    h.ls()
    for i in range(h.GetNdimensions()):
        print(i, h.GetAxis(i).GetTitle(), h.GetAxis(i).GetNbins(), h.GetAxis(i).GetBinLowEdge(1), h.GetAxis(i).GetBinUpEdge(h.GetAxis(i).GetNbins()))
    if charge == "Pos":
        h.GetAxis(5).SetRange(2, 2)
    else:
        h.GetAxis(5).SetRange(1, 1)
    hdca_vs_pt = h.Projection(0, 1)

    g_mean = TGraphErrors()
    g_mean.SetName("g_mean")
    g_mean.GetXaxis().SetTitle(hdca_vs_pt.GetYaxis().GetTitle())
    g_mean.GetYaxis().SetTitle("#mu <" + hdca_vs_pt.GetXaxis().GetTitle().replace("(", "> ("))

    g_sigma = TGraphErrors()
    g_sigma.SetName("g_sigma")
    g_sigma.GetXaxis().SetTitle(hdca_vs_pt.GetYaxis().GetTitle())
    g_sigma.GetYaxis().SetTitle("#sigma <" + hdca_vs_pt.GetXaxis().GetTitle().replace("(", "> ("))

    fun = TF1("gaus", "gaus", -300, 300)
    fun = TF1("gaus(0)+pol1(3)", "gaus(0)+pol1(3)", -300, 300)
    fun.SetParameter(0, 1.1)
    fun.SetParLimits(0, 1, 10000000)
    fun.SetParLimits(2, 0, 1000)
    canbin = draw_nice_canvas("singlebin", replace=False, logy=True)
    for k in range(1, hdca_vs_pt.GetNbinsY()+1):
        hp = hdca_vs_pt.ProjectionX("hp", k, k)
        ROOT.Math.MinimizerOptions().SetStrategy(0)
        fun.SetParameter(1, hp.GetMean())
        hp.Fit(fun, "QNWW", "", -300, 300)

        def run_fit(strategy):
            ROOT.Math.MinimizerOptions().SetStrategy(strategy)
            r = hp.Fit(fun, "QINSWW")
            if not gMinuit:
                return None
            st = gMinuit.fCstatu
            if "CONVERGED" not in st:
                print("Fit in pT", "with strategy", strategy, "did not converge -> ", st)
                return None
            return r
        if 1:
            for s in range(0, 4):
                r = run_fit(s)
            if r is None:
                r = run_fit(3)
        canbin.cd()
        hp.Draw()
        fun.Draw("same")
        canbin.Modified()
        canbin.Update()
        pt_bin = [hdca_vs_pt.GetYaxis().GetBinCenter(k),  hdca_vs_pt.GetYaxis().GetBinWidth(k)/2]
        g_mean.AddPoint(pt_bin[0], fun.GetParameter(1))
        g_mean.SetPointError(g_mean.GetN()-1, pt_bin[1], fun.GetParError(1))
        g_sigma.AddPoint(pt_bin[0], fun.GetParameter(2))
        g_sigma.SetPointError(g_sigma.GetN()-1, pt_bin[1], fun.GetParError(2))

    draw_nice_canvas("mean", replace=False)
    g_mean.Draw("ALP")

    draw_nice_canvas("sigma", replace=False)
    g_sigma.Draw("ALP")

    if tag_it:
        summary_file = filename.replace("AnalysisResults.root", "download_summary.txt")
        if os.path.isfile(summary_file):
            with open(summary_file) as f:
                for i in f:
                    if "Period" in i:
                        period_name = i.replace("Period", "")
                    if "Run" in i:
                        run_name = i.replace("Run", "")
            print(period_name, run_name)
        g_mean.SetTitle(f"{period_name} {run_name}")
        g_sigma.SetTitle(f"{period_name} {run_name}")

    # update_all_canvases()
    del hdca_vs_pt
    hdca_vs_pt = None
    del h
    h = None
    return g_mean, g_sigma


def main(file_names):
    graphs = {}
    for i in file_names:
        graphs[i] = process_one_file(i)

    colors = make_color_range(len(graphs))
    first = True
    canvases = [draw_nice_canvas("mean_comparison"), draw_nice_canvas("sigma_comparison")]
    for i in graphs:
        color = colors.pop()
        for j in range(2):
            g = graphs[i][j]
            canvases[j].cd()
            g.SetLineColor(color)
            g.SetMarkerColor(color)
            g.SetLineWidth(2)
            g.SetMarkerStyle(20)
            if first:
                g.Draw("ALP")
            else:
                g.Draw("LPsame")
        first = False
    for i in canvases:
        i.BuildLegend()

    update_all_canvases()


main(argv[1:])
