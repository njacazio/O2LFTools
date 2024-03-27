#!/usr/bin/env python3

"""
Script to compare the full and standard PID
"""

import sys
if 1:
    sys.path.append('../../PerformancePlots/')
    from utils import draw_nice_canvas, draw_nice_frame, draw_nice_label, transpose_th2, getfromfile, update_all_canvases
from ROOT import TH1


def nsgigma(fname, particle):
    histograms = [getfromfile(fname, "tof-pid-qa_Full/nsigma/"+particle),
                  getfromfile(fname, "tof-pid-qa_FullGoodMatch/nsigma/"+particle)]
    histograms[0].SetName("all")
    histograms[0].SetTitle("all")
    histograms[1].SetName("goodMatch")
    histograms[1].SetTitle("goodMatch")
    for i in histograms:
        draw_nice_canvas(i.GetName())
        i.Draw("COLZ")

    can = draw_nice_canvas("projection", logy=True)
    pt_bin = [0.6, 0.65]
    pt_bin = [i.GetXaxis().FindBin(pt_bin[0]),
              i.GetXaxis().FindBin(pt_bin[1])]
    projections = [i.ProjectionY(i.GetName()+"_proj", *pt_bin) for i in histograms]
    projections[0].SetBit(TH1.kNoTitle)
    projections[0].SetBit(TH1.kNoStats)
    projections[0].Draw()
    projections[0].SetLineColor(2)
    projections[0].SetLineStyle(2)
    projections[1].Draw("SAME")
    leg = can.BuildLegend()
    leg.SetHeader(f"{histograms[0].GetXaxis().GetBinLowEdge(pt_bin[0]):.2f} < p_{{T}} < {histograms[0].GetXaxis().GetBinUpEdge(pt_bin[1]):.2f} GeV/c")
    
    can = draw_nice_canvas("diff", logy=True)
    hdiff=  projections[0].DrawCopy()
    hdiff.Add(projections[1], -1)
    hdiff.SetTitle("all - goodMatch")
    hdiff.GetYaxis().SetTitle("all - goodMatch")

    can = draw_nice_canvas("ratio", logy=False)
    hratio=  projections[0].DrawCopy()
    hratio.SetTitle("all/goodMatch")
    hratio.GetYaxis().SetTitle("all/goodMatch")
    hratio.Divide(projections[1])

def beta(fname):
    histograms = [getfromfile(fname, "tof-pid-beta-qa/tofbeta/inclusive"),
                  getfromfile(fname, "tof-pid-beta-qa_GoodMatch/tofbeta/inclusive")]
    print(histograms[0].GetXaxis().GetTitle())
    print(histograms[0].GetYaxis().GetTitle())
    print(histograms[0].GetZaxis().GetTitle())
    histograms[0] = histograms[0].Project3D("yx")
    histograms[0].SetName("all")
    histograms[0].SetTitle("all")
    histograms[0].GetXaxis().SetRangeUser(0, 5)
    histograms[1] = histograms[1].Project3D("yx")
    histograms[1].SetName("goodMatch")
    histograms[1].SetTitle("goodMatch")
    histograms[1].GetXaxis().SetRangeUser(0, 5)
    for i in histograms:
        draw_nice_canvas(i.GetName())
        i.Draw("COLZ")

    can = draw_nice_canvas("projection", logy=False, logz=False)
    pt_bin = [0.6, 0.65]
    pt_bin = [i.GetXaxis().FindBin(pt_bin[0]),
              i.GetXaxis().FindBin(pt_bin[1])]
    projections = [i.ProjectionY(i.GetName()+"_proj", *pt_bin) for i in histograms]
    projections[0].SetBit(TH1.kNoTitle)
    projections[0].SetBit(TH1.kNoStats)
    projections[0].Draw()
    projections[0].SetLineColor(2)
    projections[0].SetLineStyle(2)
    projections[1].Draw("SAME")
    leg = can.BuildLegend()
    leg.SetHeader(f"{histograms[0].GetXaxis().GetBinLowEdge(pt_bin[0]):.2f} < p_{{T}} < {histograms[0].GetXaxis().GetBinUpEdge(pt_bin[1]):.2f} GeV/c")
    
    can = draw_nice_canvas("diff", logy=False, logz=False)
    hdiff=  projections[0].DrawCopy()
    hdiff.Add(projections[1], -1)
    hdiff.SetTitle("all - goodMatch")
    hdiff.GetYaxis().SetTitle("all - goodMatch")

    can = draw_nice_canvas("ratio", logy=False)
    hratio=  projections[0].DrawCopy()
    hratio.SetTitle("all/goodMatch")
    hratio.GetYaxis().SetTitle("all/goodMatch")
    hratio.Divide(projections[1])


def main(fname="/tmp/TOFBeta.root", particle="Pi"):
    # nsgigma(fname, particle)
    beta(fname)

    update_all_canvases()


main()
