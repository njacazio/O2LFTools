#!/usr/bin/env python3

from ROOT import gMinuit, TFile, TGraphErrors, TF1, TColor, TLegend
import ROOT

from sys import argv
import sys
if 1:
    sys.path.append('../../PerformancePlots/')
    from utils import draw_nice_canvas, draw_nice_frame, draw_nice_label, transpose_th2, getfromfile, update_all_canvases
from numpy import sqrt


def main(filename="/tmp/AnalysisResults.root"):
    h = getfromfile(filename, "perf-k0s-resolution/K0sDauResolution/h3_tpc_vs_pid_hypothesis")

    particles = ["El", "Mu", "Pi", "Ka", "Pr", "De", "Tr", "He", "Al", "None", "None"]
    hp = {}

    for i in range(1, h.GetZaxis().GetNbins() + 1):
        h.GetZaxis().SetRange(i, i)
        p = particles[i-1]
        hp[p] = h.Project3D("yx")
        if hp[p].GetEntries() == 0:
            continue
        hp[p].SetName(f"PID {p}")
        hp[p].SetDirectory(0)
        draw_nice_canvas(f"tpc{p}")
        hp[p].Draw("colz")

    update_all_canvases()


main()
