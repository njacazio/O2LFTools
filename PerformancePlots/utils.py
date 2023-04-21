#!/usr/bin/env python3

from ROOT import TCanvas, TLegend, TLine, TLatex


nice_labels = []


def draw_nice_label(l, x=0.7, y=0.5, s=0.035, yd=0, align=11):
    if type(l) is not str:
        raise ValueError(f"Label {l} must be a string, but is a type {type(l)}")
    latex = TLatex(x, y+yd, l)
    latex.SetNDC()
    latex.SetTextFont(42)
    latex.SetTextSize(s)
    latex.SetTextAlign(align)
    latex.Draw()
    nice_labels.append(latex)
    return latex


nice_canvases = {}


def draw_nice_canvas(name, x=800, y=800, logx=False, logy=False, logz=True, title=None, replace=True, extend_right=False):
    global nice_canvases
    if not replace and name in nice_canvases:
        c = nice_canvases[name]
        c.cd()
        if title is not None:
            c.SetTitle(title)
        return c
    if title is None:
        title = name
    right_margin = 0.05
    if extend_right:
        x = 1200
        right_margin = 0.317195
    c = TCanvas(name, title, x, y)
    c.SetLogx(logx)
    c.SetLogy(logy)
    c.SetLogz(logz)
    c.SetTicky()
    c.SetTickx()
    c.SetLeftMargin(0.15)
    c.SetBottomMargin(0.15)
    c.SetRightMargin(right_margin)
    c.SetTopMargin(0.05)
    c.Draw()
    nice_canvases[name] = c
    return c


nice_frames = {}


def draw_nice_frame(c, x, y, xt, yt):
    c.cd()
    global nice_frames
    if type(x) is not list:
        x = [x.GetXaxis().GetBinLowEdge(1),
             x.GetXaxis().GetBinUpEdge(x.GetNbinsX())]
    if type(y) is not list:
        if "TH2" in y.ClassName():
            y = [y.GetYaxis().GetBinLowEdge(1),
                 y.GetYaxis().GetBinUpEdge(y.GetYaxis().GetNbins())]
        else:
            y = [y.GetMinimum(), y.GetMaximum()]
    if not type(xt) is str:
        xt = xt.GetXaxis().GetTitle()
    if not type(yt) is str:
        yt = yt.GetYaxis().GetTitle()
    frame = c.DrawFrame(x[0], y[0], x[1], y[1], f";{xt};{yt}")
    frame.GetYaxis().SetTitleSize(0.04)
    frame.GetXaxis().SetTitleSize(0.04)
    frame.GetXaxis().SetTitleOffset(1.25)
    frame.SetDirectory(0)
    nice_frames[c.GetName()] = frame
    return frame
