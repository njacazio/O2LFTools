#!/usr/bin/env python3

from ROOT import TCanvas, TColor, TLatex, TH1, gPad, TFile, TH2F, gStyle
import numpy as np


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


def getfromfile(filename, objname="", alternatives=None):
    f = TFile(filename, "READ")
    if type(objname) is int:
        objname = f.GetListOfKeys().At(objname).GetName()
    obj = f.Get(objname)
    if not obj:
        if alternatives is not None:
            if type(alternatives) is not list:
                alternatives = [alternatives]
            print("Trying alternatives to", objname, "trying", alternatives[0], "in", alternatives)
            return getfromfile(filename, objname=alternatives.pop(0), alternatives=alternatives)
        f.ls()
        raise ValueError("Did not find", objname, "in", filename)
    if "Directory" in obj.ClassName():
        obj.ls()
    if "TH" in obj.ClassName() and "Sparse" not in obj.ClassName():
        obj.SetDirectory(0)
    f.Close()
    return obj


transposed_histos = {}


def transpose_th2(h):
    htransposed = TH2F(f"htransposed_{h.GetName()}", f"htransposed_{h.GetName()};{h.GetYaxis().GetTitle()};{h.GetXaxis().GetTitle()}", h.GetYaxis().GetNbins(),
                       h.GetYaxis().GetXmin(), h.GetYaxis().GetXmax(), h.GetXaxis().GetNbins(), h.GetXaxis().GetXmin(), h.GetXaxis().GetXmax())
    for ix in range(1, h.GetNbinsX() + 1):
        for iy in range(1, h.GetNbinsY() + 1):
            htransposed.SetBinContent(iy, ix, h.GetBinContent(ix, iy))
            htransposed.SetBinError(iy, ix, h.GetBinError(ix, iy))
    n = f"{h.GetName()}"
    if n in transposed_histos:
        n = f"{n}_{len(transposed_histos)}"
    transposed_histos[n] = htransposed
    return htransposed


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
        # right_margin = 0.317195
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


def update_all_canvases(wait=True):
    for c in nice_canvases.values():
        c.Modified()
        c.Update()
    if wait:
        input("Press enter to continue")


nice_frames = {}


def make_color_range(ncolors, simple=False):
    if ncolors <= 0:
        print("ncolors must be > 0")
    if ncolors == 1:
        simple = True
    if simple:
        if ncolors <= 2:
            colors = ['#e41a1c', '#377eb8']
        elif ncolors <= 3:
            colors = ['#e41a1c', '#377eb8', '#4daf4a']
        elif ncolors <= 4:
            colors = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3']
        elif ncolors < 5:
            colors = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00']
        else:
            colors = ['#00000', '#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#a65628', '#f781bf']
        # print("Using colors", colors)
        if len(colors) < ncolors:
            print("Not enough colors for simple", ncolors, "using, continous scale")
            return make_color_range(ncolors=ncolors, simple=False)
        return [TColor.GetColor(i) for i in colors]
    NRGBs = 5
    NCont = 256
    NCont = ncolors
    stops = np.array([0.00, 0.30, 0.61, 0.84, 1.00])
    red = np.array([0.00, 0.00, 0.57, 0.90, 0.51])
    green = np.array([0.00, 0.65, 0.95, 0.20, 0.00])
    blue = np.array([0.51, 0.55, 0.15, 0.00, 0.10])
    FI = TColor.CreateGradientColorTable(NRGBs,
                                         stops, red, green, blue, NCont)
    colors = []
    for i in range(NCont):
        colors.append(FI + i)
    colors = np.array(colors, dtype=np.int32)
    gStyle.SetPalette(NCont, colors)
    return [int(i) for i in colors]


def set_nice_frame(h):
    h.SetBit(TH1.kNoStats)
    h.SetBit(TH1.kNoTitle)
    h.GetYaxis().SetTitleSize(0.04)
    h.GetXaxis().SetTitleSize(0.04)
    h.GetXaxis().SetTitleOffset(1.25)
    h.SetDirectory(0)


def draw_nice_frame(c, x, y, xt, yt):
    if c is None:
        gPad.cd()
    else:
        c.cd()
    global nice_frames
    if type(x) is not list:
        x = [x.GetXaxis().GetBinLowEdge(1),
             x.GetXaxis().GetBinUpEdge(x.GetNbinsX())]
    else:
        if len(x) != 2:
            raise ValueError(f"X range must be a list of two elements, but is {x}")
        x = [float(x[0]), float(x[1])]
    if type(y) is not list:
        if "TH2" in y.ClassName():
            y = [y.GetYaxis().GetBinLowEdge(1),
                 y.GetYaxis().GetBinUpEdge(y.GetYaxis().GetNbins())]
        else:
            y = [y.GetMinimum(), y.GetMaximum()]
    else:
        if len(y) != 2:
            raise ValueError(f"Y range must be a list of two elements, but is {y}")
        y = [float(y[0]), float(y[1])]
    if not type(xt) is str:
        xt = xt.GetXaxis().GetTitle()
    if not type(yt) is str:
        yt = yt.GetYaxis().GetTitle()
    frame = c.DrawFrame(x[0], y[0], x[1], y[1], f";{xt};{yt}")
    set_nice_frame(frame)
    nice_frames[c.GetName()] = frame
    return frame
