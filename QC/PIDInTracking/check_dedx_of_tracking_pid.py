#!/usr/bin/env python3

"""
Script to check the dE/dx of the PID in the tracking
"""


import argparse
if 1:
    import sys
    sys.path.append('../../PerformancePlots/')
from utils import draw_nice_canvas, draw_nice_frame, draw_nice_label
from ROOT import TFile, TGraphErrors, TF1, TH1, TColor, TLegend


def main(filename, draw_single=False, avoid=None, saveas=None):
    file = TFile(filename, "READ")
    histograms = {}
    for i in range(9):
        histograms[f"tpc-pid-qa-signal/event/tpcsignal_{i}"] = None
    for i in histograms:
        histograms[i] = file.Get(i)
        histograms[i].SetDirectory(0)
        print(i,
              histograms[i].GetXaxis().GetTitle(), histograms[i].GetXaxis().GetNbins(),
              histograms[i].GetYaxis().GetTitle(), histograms[i].GetYaxis().GetNbins(),
              histograms[i].GetZaxis().GetTitle(), histograms[i].GetZaxis().GetNbins())
    file.Close()
    particle_name = ["electron", "muon", "pion", "kaon", "proton", "deuteron", "triton", "helium3", "helium4", "all"]
    particle_colors = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#ffff33', '#a65628', '#f781bf', '#999999', "#000000"]
    particle_colors = [TColor.GetColor(i) for i in particle_colors]
    charge_name = ["negative", "positive", "all"]
    projections = {}
    for i in histograms:
        pname = particle_name[int(i.split("_")[-1])]
        for j in range(1, histograms[i].GetNbinsZ()+1):
            h = histograms[i]
            h.GetZaxis().SetRange(j, j)
            hp = h.Project3D("yx")
            hp.SetName(f"{pname}_{charge_name[j-1]}")
            hp.SetTitle(f"{pname} {charge_name[j-1]}")
            hp.SetBit(TH1.kNoStats)
            hp.SetBit(TH1.kNoTitle)
            hp.SetLineColor(particle_colors[int(i.split("_")[-1])])
            hp.SetMarkerColor(particle_colors[int(i.split("_")[-1])])
            hp.SetFillColor(particle_colors[int(i.split("_")[-1])])
            hp.SetDirectory(0)
            if draw_single:
                can = draw_nice_canvas(f"{i}_{j}")
                hp.Draw("colz")
                draw_nice_label(f"{pname} {charge_name[j-1]}")
                can.Modified()
                can.Update()
            projections[f"{pname} {charge_name[j-1]}"] = hp

    can = draw_nice_canvas("ALL")
    draw_nice_frame(can, [0, 3], [0, 1000],
                    projections[list(projections.keys())[0]],
                    projections[list(projections.keys())[0]])
    profiles = []
    for i in projections:
        doskip = False
        if avoid is not None:
            for j in avoid:
                if j in i:
                    doskip = True
                    break
        if doskip:
            continue

        projections[i].Draw("same")
        profiles.append(projections[i].ProfileX())
        profiles[-1].SetLineColor(projections[i].GetLineColor())
        profiles[-1].SetMarkerColor(1)
        profiles[-1].SetMarkerStyle(4)

    leg = can.BuildLegend(0.6, 0.6, 0.9, 0.9)
    leg.GetListOfPrimitives().RemoveAt(0)
    for i in profiles:
        i.Draw("SAME")

    can.Modified()
    can.Update()
    if saveas is not None:
        can.SaveAs(saveas)
    input("Press enter to continue...")


if __name__ == "__main__":
    paser = argparse.ArgumentParser()
    paser.add_argument("input", help="Input file")
    paser.add_argument("--avoid", "-a", default=None, help="Path to O2Physics", nargs="+")
    paser.add_argument("--saveas", "-s", default=None, help="Save file for canvas")
    args = paser.parse_args()

    main(args.input, avoid=args.avoid, saveas=args.saveas)
