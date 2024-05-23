#!/usr/bin/env python3

"""
Script to compare the full and standard PID
"""

import sys
if 1:
    sys.path.append('../../PerformancePlots/')
    from utils import draw_nice_canvas, getfromfile, update_all_canvases, set_nice_frame, draw_nice_legend


def main(fname1="/tmp/MC.root",
         fname2=None,
         particle="Pi"):
    if fname2 is None:
        fname2 = fname1
    else:
        print("Using file 1", fname1, "and file 2", fname2)
    histograms = [getfromfile(fname1, "tof-pid-qa/nsigma/"+particle),
                  getfromfile(fname2, "tof-pid-qa_Full/nsigma/"+particle)]
    histograms[0].SetName("tiny")
    histograms[1].SetName("full")
    histograms[0].SetTitle("tiny")
    histograms[1].SetTitle("full")
    for i in histograms:
        set_nice_frame(i)
        draw_nice_canvas(i.GetName(), replace=False)
        i.Draw("COLZ")

    draw_nice_canvas("projection", replace=False)
    pt_bin = [1.0, 1.1]
    projections = [i.ProjectionY(i.GetName()+"_proj",
                                 i.GetXaxis().FindBin(pt_bin[0]),
                                 i.GetXaxis().FindBin(pt_bin[1])) for i in histograms]
    projections[0].SetLineColor(2)
    projections[0].SetLineStyle(2)

    projections[1].Draw()
    projections[0].Draw("SAME")

    leg = draw_nice_legend()
    for i in projections:
        set_nice_frame(i)
        leg.AddEntry(i)

    # Checking the agreement
    total = [0, 0]
    for i in range(projections[0].GetNbinsX()):
        x = projections[0].GetXaxis().GetBinCenter(i)
        if abs(x) > 6.2:
            continue

        total[0] += projections[0].GetBinContent(i)
        total[1] += projections[1].GetBinContent(i)

    if total[0] != total[1]:
        print("Total counts differ by", total[1]-total[0])
    else:
        print("All good")
    update_all_canvases()


# main()
main("/tmp/pid/out/NotMerged.root",
     "/tmp/pid/out/NotMerged.root")


main("/tmp/pid/out/Merged.root",
     "/tmp/pid/out/Merged.root")

main("/tmp/pid/out/Merged.root",
     "/tmp/pid/out/NotMerged.root")

main("/tmp/pid/out/NotMerged.root",
     "/tmp/pid/out/Merged.root")
