#!/usr/bin/env python3

from ROOT import gMinuit, TFile, TGraphErrors, TF1, TColor, TLegend
import ROOT

from sys import argv
import sys
if 1:
    sys.path.append('../../PerformancePlots/')
    from utils import draw_nice_canvas, draw_nice_frame, getfromfile, update_all_canvases


def main(filenames=["/tmp/perf-k0s-resolution_h2_masspTsigma_AllPIDs.root",
                    "/tmp/perf-k0s-resolution_h2_masspTsigma.root",
                    "/tmp/perf-k0s-resolution_h2_masspTsigma_yesTOF.root"],
         tags=["Standard", "Pion PID", "Daughter with TOF"]):

    input_objects = []
    for i in filenames:
        input_objects.append(getfromfile(i, 0))
        input_objects[-1].SetName(i)

    colors = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#ffff33', '#a65628', '#f781bf']
    if len(filenames) < 8:
        colors = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#a65628']
    colors.append('#999999')
    can = draw_nice_canvas("comparison")
    leg = TLegend(0.2, 0.66, 0.7, 0.81)
    per_tag = {}
    frame = None
    for i in input_objects:
        t = tags.pop(0)
        per_tag[t] = []
        if "TGraph" in i.ClassName():
            objects_to_draw = [i]
        else:
            objects_to_draw = i.GetListOfPrimitives()
        for j in objects_to_draw:
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
            print("Drawing", j)
            per_tag[t].append(j)
            leg.AddEntry(j)
    leg.Draw()

    print(per_tag)

    can = draw_nice_canvas("ratio")
    legratio = TLegend(0.2, 0.66, 0.7, 0.81)
    frame_ratio = frame.DrawCopy()
    frame_ratio.GetYaxis().SetTitle("Ratio")
    frame_ratio.GetYaxis().SetRangeUser(0.5, 1.5)
    frame_ratio.GetYaxis().SetRangeUser(0., 10)
    firsttag = list(per_tag.keys())[0]
    for i in per_tag:
        if i == firsttag:
            continue
        for idx, j in enumerate(per_tag[i]):
            j = j.DrawClone("LPSAME")
            j.SetTitle(j.GetTitle() + "/" + per_tag[firsttag][idx].GetTitle())
            legratio.AddEntry(j)
            for k in range(j.GetN()):
                x = j.GetX()[k]
                reference = per_tag[firsttag][idx].Eval(x)
                if reference <= 0:
                    print("Warnning, reference is 0 for tag", f"'{firsttag}'")
                    continue
                j.SetPoint(k, x, j.GetY()[k] / reference)
    legratio.Draw()

    update_all_canvases()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Compare different files and do ratios')
    parser.add_argument('filenames', metavar='F', type=str, nargs='+',
                        help='Files to compare')
    parser.add_argument('--tags', "-t", metavar='T', type=str, nargs='+',
                        default=None,
                        help='Tags for the files')
    args = parser.parse_args()
    tags = args.tags
    if tags is None:
        tags = [i.split("_masspT")[-1].strip("_").strip(".root") for i in args.filenames]
    main(args.filenames, tags)
