#!/usr/bin/env python3

from ROOT import gMinuit, TFile, TGraphErrors, TF1, TColor, TLegend
import ROOT

from sys import argv
import sys
if 1:
    sys.path.append('../../PerformancePlots/')
    from utils import draw_nice_canvas, draw_nice_frame, draw_nice_label, transpose_th2, getfromfile, update_all_canvases
from numpy import sqrt


def main(filenames=["/tmp/perf-k0s-resolution_h2_masspTsigma.root",
                    "/tmp/perf-k0s-resolution_h2_masspTsigma_yesTOF.root"],
         tags=["Standard", "Daughter with TOF"]):

    canvases = []
    for i in filenames:
        canvases.append(getfromfile(i, 0))
        canvases[-1].SetName(i)

    colors = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#ffff33', '#a65628', '#f781bf', '#999999']
    can = draw_nice_canvas("comparison")
    leg = TLegend(0.2, 0.66, 0.7, 0.81)
    per_tag = {}
    frame = None
    for i in canvases:
        t = tags.pop(0)
        per_tag[t] = []
        for j in i.GetListOfPrimitives():
            if "TGraph" not in j.ClassName():
                continue
            if can.GetListOfPrimitives().GetSize() == 0:
                frame = draw_nice_frame(can,
                                        x=[0, 10],
                                        y=[0, 0.01],
                                        xt=j.GetXaxis().GetTitle(),
                                        yt=j.GetYaxis().GetTitle())
            col = TColor.GetColor(colors.pop(0))
            j.SetLineColor(col)
            j.SetFillColor(col)
            j.SetFillStyle(0)
            j.SetMarkerColor(col)
            j.SetMarkerStyle(20)
            j.SetMarkerSize(0.5)
            j.SetTitle(j.GetTitle() + f" ({t})")
            j = j.DrawClone("LPSAME")
            per_tag[t].append(j)
            leg.AddEntry(j)
    leg.Draw()

    can = draw_nice_canvas("ratio")
    legratio = TLegend(0.2, 0.66, 0.7, 0.81)
    frame_ratio = frame.DrawCopy()
    frame_ratio.GetYaxis().SetTitle("Ratio")
    frame_ratio.GetYaxis().SetRangeUser(0.5, 1.5)
    firsttag = list(per_tag.keys())[0]
    for i in per_tag:
        if i == firsttag:
            continue
        for idx, j in enumerate(per_tag[i]):
            j = j.DrawClone("LPSAME")
            j.SetTitle(j.GetTitle()+ "/" + per_tag[firsttag][idx].GetTitle())
            legratio.AddEntry(j)
            for k in range(j.GetN()):
                x = j.GetX()[k]
                j.SetPoint(k, x, j.GetY()[k] / per_tag[firsttag][idx].Eval(x))
    legratio.Draw()

    update_all_canvases()


main()
