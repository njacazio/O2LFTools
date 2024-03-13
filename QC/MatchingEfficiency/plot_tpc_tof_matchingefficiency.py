#!/usr/bin/env python3

from ROOT import gMinuit, TFile, TGraphErrors, TF1, TColor, TLegend
import ROOT

from sys import argv
import sys
if 1:
    sys.path.append('../../PerformancePlots/')
    from utils import draw_nice_canvas, draw_nice_frame, draw_nice_label, transpose_th2, getfromfile, update_all_canvases
from numpy import sqrt


def process_one_file(filename, pos=True, variable="pt"):
    dn = 'qa-efficiency/Data'
    if pos:
        dn += '/pos'
    else:
        dn += '/neg'
    dn += '/'+variable
    num = getfromfile(filename, dn + "/its_tpc_tof")
    den = getfromfile(filename, dn + "/its_tpc")

    num.SetTitle(filename.split("/")[-1].replace(".root", ""))
    num.Divide(num, den, 1, 1, "B")
    return num


def main(fnames=["/tmp/eff_apass3.root",
                 "/tmp/eff_apass1.root"]):
    eff_pos = {}
    eff_neg = {}
    colors = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#ffff33', '#a65628', '#f781bf', '#999999']
    for i in fnames:
        col = colors.pop(0)
        col = TColor.GetColor(col)
        eff_pos[i] = process_one_file(i, pos=True)
        eff_neg[i] = process_one_file(i, pos=False)
        eff_pos[i].SetLineColor(col)
        eff_neg[i].SetLineColor(col)
        eff_pos[i].SetMarkerColor(col)
        eff_neg[i].SetMarkerColor(col)
        eff_pos[i].SetMarkerStyle(20)
        eff_neg[i].SetMarkerStyle(24)

    draw_nice_frame(draw_nice_canvas("pos"),
                    xt="p_{T} (GeV/c)",
                    yt="Efficiency",
                    y=[0, 1.1],
                    x=[0, 5])
    leg = TLegend(0.25, 0.77, 0.7, 0.9)
    for i in eff_pos:
        eff_pos[i].Draw("SAME")
        leg.AddEntry(eff_pos[i])
    leg.Draw()

    draw_nice_frame(draw_nice_canvas("neg"),
                    xt="p_{T} (GeV/c)",
                    yt="Efficiency",
                    y=[0, 1.1],
                    x=[0, 5])
    for i in eff_neg:
        eff_neg[i].Draw("SAME")

    draw_nice_frame(draw_nice_canvas("pos_neg"),
                    xt="p_{T} (GeV/c)",
                    yt="Efficiency",
                    y=[0, 1.1],
                    x=[0, 5])
    legcharge = TLegend(0.25, 0.64, 0.7, 0.73)
    for i in eff_neg:
        eff_pos[i].Draw("SAME")
        eff_neg[i].Draw("SAME")

    legcharge.AddEntry(eff_pos[fnames[0]], "Positive")
    legcharge.AddEntry(eff_neg[fnames[0]], "Negative")
    leg.Draw()
    legcharge.Draw()
    update_all_canvases()


main()
