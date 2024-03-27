#!/usr/bin/env python3


from ROOT import TFile, TCanvas, TH1
if 1:
    import sys
    sys.path.append('../../PerformancePlots/')
from utils import draw_nice_canvas, draw_nice_frame, draw_nice_label, set_nice_frame
from ROOT import TFile, TGraphErrors, TF1, TH1, TColor, TLegend, TH1F, TObjArray


def main():
    print("Hello")

    def get(fn, tag="", cf=False, subdir=None):
        print(fn)
        f = TFile(fn, "READ")
        f.ls()
        d = f.Get("lfprop-study")
        if subdir is not None:
            d = d.Get(subdir)
        if cf:
            d = f.Get("c-f-filter/TrackCuts/V0Before/NegDaughter")
        d.ls()
        hh = {}
        for i in d.GetListOfKeys():
            if "TH" not in i.GetClassName():
                continue
            print(i.GetName())
            hh[i.GetName()] = d.Get(i.GetName())
            hh[i.GetName()].SetDirectory(0)
            hh[i.GetName()].SetName(i.GetName()+tag)
            hh[i.GetName()].SetTitle(tag)
        f.Close()
        return hh

    # histo1 = get("/tmp/AnalysisResults_TRKCHECK.root", tag="old")
    # histo2 = get("/tmp/AnalysisResults_TRKCHECK_latest.root", tag="new")
    # histo1 = get("/tmp/AnalysisResults_TRKCHECK_old.root", tag="old")
    # histo2 = get("/tmp/AnalysisResults_TRKCHECK_new.root", tag="new")
    histo1 = get("/tmp/AnalysisResults_old.root", tag="old")
    histo2 = get("/tmp/AnalysisResults_new.root", tag="new")
    histo1_iu = get("/tmp/AnalysisResults_old.root", tag="old", subdir="IU")
    histo2_iu = get("/tmp/AnalysisResults_new.root", tag="new", subdir="IU")
    # histo1 = get("/tmp/AnalysisResults_TRKCHECK_oldnocov.root", tag="old")
    # histo2 = get("/tmp/AnalysisResults_TRKCHECK_newnocov.root", tag="new")
    # histo2 = get("/tmp/AnalysisResults_TRKCHECK_newnocoll.root", tag="new")
    # histo1 = get("/tmp/AnalysisResults_TRKCHECK_nocoll.root", tag="old")

    histo1_cf = get("/tmp/AnalysisResults_old.root", tag="old", cf=True)
    histo2_cf = get("/tmp/AnalysisResults_new.root", tag="new", cf=True)

    hdrawn = {}

    def draw(hn="hPt", hd=histo1, opt=""):
        if 0:
            pn = ["El", "Mu", "Pi", "Ka", "Pr", "De", "Tr", "He", "Al"]
            pn = ["El", "Pi", "Ka", "Pr", "De", "Tr", "He", "Al"]
            h = hd[hn+pn[0]].Clone(f"{hd[hn+pn[0]].GetName()}_all")
            h.SetTitle(h.GetTitle().replace(pn[0], ""))
            vartit = {"hPt": "p_{T} (GeV/c)", "hDCAxy": "DCA_{xy} (cm)"}
            h.GetXaxis().SetTitle(vartit[hn])
            h.GetYaxis().SetTitle("Counts")
            h.SetBit(TH1.kNoStats)
            h.Reset()
            for i in pn:
                h.Add(hd[hn+i])
        else:
            h = hd[hn]
        h.Draw(opt)
        h.SetLineWidth(2)
        if "old" in h.GetName():
            h.SetLineColor(2)
            h.SetLineStyle(2)
        hdrawn[h.GetName()] = h

    canvases = {}

    def dodraw(var="hPt", hnew=histo2, hold=histo1, tag=""):
        c = draw_nice_canvas("c"+var+tag)
        draw(var, hnew)
        draw(var, hold, "same")
        leg = c.BuildLegend()
        leg.SetHeader(var)
        leg.GetListOfPrimitives().RemoveAt(0)
        canvases[var] = c
        canvases["leg"+var] = leg
        c.Modified()
        c.Update()

    dodraw("hPt")
    dodraw('hDCAxy')
    dodraw('hPt', hnew=histo2_iu, hold=histo1_iu, tag="IU")
    dodraw('hDCAxy', hnew=histo2_iu, hold=histo1_iu, tag="IU")

    # CF
    dodraw("DCAXY", hnew=histo2_cf, hold=histo1_cf)

    input("Press enter to continue")


main()
