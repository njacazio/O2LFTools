#!/usr/bin/env python3

import sys
if 1:
    sys.path.append('../../PerformancePlots/')
    from utils import draw_nice_canvas, draw_nice_frame, draw_nice_label, transpose_th2, update_all_canvases

from ROOT import TFile, TColor


def main():
    def get(fn):
        f = TFile(fn, "READ")
        h = f.Get(f.GetListOfKeys().At(0).GetName())
        h.SetTitle(fn.split("/")[-1].replace(".root", ""))
        return h
    obj = []
    for i in ["/tmp/aside.root", "/tmp/cside.root"]:
        obj.append(get(i))

    draw_nice_canvas("compare")
    colors = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#a65628']
    for i in obj:
        col = colors.pop(0)
        col = TColor.GetColor(col)
        i.SetLineColor(col)
        i.SetMarkerColor(col)


    obj[0].Draw("ALP")
    obj[1].Draw("LP same")

    draw_nice_canvas("ratio")
    ratio = obj[0].DrawClone("ALP")
    for i in range(0, ratio.GetN()):
        ratio.GetY()[i] = obj[0].GetY()[i] / obj[1].GetY()[i]
        ratio.GetEY()[i] = ratio.GetY()[i] * (obj[0].GetEY()[i] / obj[0].GetY()[i] + obj[1].GetEY()[i] / obj[1].GetY()[i])
    ratio.SetTitle("A-side/C-side")
    update_all_canvases()

main()