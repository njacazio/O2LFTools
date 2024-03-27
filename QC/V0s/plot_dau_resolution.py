#!/usr/bin/env python3

from ROOT import gMinuit, TFile, TGraphErrors, TF1, TColor, TLegend
import ROOT

from sys import argv
import sys
if 1:
    sys.path.append('../../PerformancePlots/')
    from utils import draw_nice_canvas, draw_nice_frame, draw_nice_label, transpose_th2, update_all_canvases


def process_one_file(filename, tag=None):
    file = TFile(filename, "READ")
    thn = file.Get("perf-k0s-resolution/thn_mass")
    file.Close()

    draw_nice_canvas("mass_vs_pt")
    mass_vs_pt = thn.Projection(1, 0)
    mass_vs_pt.Draw("COLZ")
    
    draw_nice_canvas("dau1_vs_pt")
    dau1_vs_pt = thn.Projection(1, 6)
    dau1_vs_pt.Draw("COLZ")

    draw_nice_canvas("dau2_vs_pt")
    dau2_vs_pt = thn.Projection(1, 7)
    dau2_vs_pt.Draw("COLZ")

    update_all_canvases()

def main(filenames,
         tags={"150658": "LHC15o",
               "150796": "LHC23k6c_pass1",
               "150642": "LHC23_PbPb_pass1_sampling",
               "151351": "LHC15n_pass5",
               "150994": "LHC23g",
               "152893": "LHC23f_pass1",
               "/tmp/AnalysisResults_apass1.root": "LHC23zzh_apass1_544124",
               "/tmp/New.root": "LHC23k6d",
               "156569": "LHC23k6d",
               "156999": "LHC22o_pass5_skimmed_QC1",
               "/tmp/AnalysisResults.root": "LHC23zzh_apass2_544124"},
         only={"150642": "19415",
               "150796": "asd",
               "151351": "asd",
               "152893": "asd"}):
    results = []
    for i in enumerate(filenames):
        hasit = None
        for j in only:
            if j in i[1]:
                hasit = True
                break
        if hasit:
            if only[j] not in i[1]:
                continue
        t = None
        for j in tags:
            if j in i[1]:
                t = tags[j]
                break
        print(i[1], t)
        results.append(process_one_file(i[1], tag=t))
        # input("Press enter to continue...")
    legs = []
    for i in results[0]:
        range_x = [0, 10]
        if "VsRadius" in i:
            range_x = [0, 50]
        range_y = [0, 0.05]
        if i.endswith("mean"):
            range_y = [0.49, 0.52]

        can = draw_nice_canvas(i)
        draw_nice_frame(can,
                        range_x,
                        range_y,
                        results[0][i].GetXaxis().GetTitle(),
                        results[0][i].GetYaxis().GetTitle())
        colors = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#a65628']
        colors = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#ffff33', '#a65628', '#f781bf', '#999999']
        leg = TLegend(0.5, 0.5, 0.9, 0.9)
        legs.append(leg)
        for j in enumerate(results):
            if i not in j[1]:
                continue
            col = colors.pop(0)
            col = TColor.GetColor(col)
            j[1][i].Draw("LPsame")
            j[1][i].SetLineWidth(2)
            j[1][i].SetLineColor(col)
            j[1][i].SetMarkerColor(col)
            leg.AddEntry(j[1][i])
        leg.Draw()
        can.Modified()
        can.Update()

    input("Press enter to continue...")


main(argv[1:])
