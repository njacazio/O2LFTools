#!/usr/bin/env python3

"""
Script to compare the full and standard PID
"""

import sys
if 1:
    sys.path.append('../../PerformancePlots/')
    from utils import draw_nice_canvas, draw_nice_frame, draw_nice_label, transpose_th2, getfromfile, update_all_canvases


def main(fname="/tmp/MC.root", particle="Pi"):
    histograms = [getfromfile(fname, "tof-pid-qa/nsigma/"+particle),
                  getfromfile(fname, "tof-pid-qa_Full/nsigma/"+particle)]
    histograms[0].SetName("tiny")
    histograms[1].SetName("full")
    for i in histograms:
        draw_nice_canvas(i.GetName())
        i.Draw("COLZ")

    draw_nice_canvas("projection")
    pt_bin = [1.0, 1.1]
    projections = [i.ProjectionY(i.GetName()+"_proj",
                                 i.GetXaxis().FindBin(pt_bin[0]),
                                 i.GetXaxis().FindBin(pt_bin[1])) for i in histograms]
    projections[0].Draw()
    projections[0].SetLineColor(2)
    projections[0].SetLineStyle(2)
    projections[1].Draw("SAME")

    update_all_canvases()


main()
