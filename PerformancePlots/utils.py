#!/usr/bin/env python3

from ROOT import TCanvas, TLegend, TLine, TLatex


nice_labels = []


def draw_nice_label(l, x=0.7, y=0.5, s=0.035, yd=0, align=11):
    latex = TLatex(x, y+yd, l)
    latex.SetNDC()
    latex.SetTextFont(42)
    latex.SetTextSize(s)
    latex.SetTextAlign(align)
    latex.Draw()
    nice_labels.append(latex)
    return latex


nice_canvases = {}