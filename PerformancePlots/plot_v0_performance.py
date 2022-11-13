#!/usr/bin/env python3

"""
Script to plot the V0 performance plots
"""

from ROOT import TFile, gPad, TH1, TLine, TF1
from utils import draw_nice_canvas, draw_nice_label
import argparse


def main(fname, rebin=2,
         tag="LHC22f",
         particle="K0s"):
    f = TFile(fname, "READ")
    # f.ls()
    xrange = [0.43, 0.54]
    fitrange = [0.48, 0.52]
    if particle in ["Lambda", "AntiLambda"]:
        xrange = [1.06, 1.15]
        fitrange = [1.1, 1.14]
        dn = f"qa-k0s-tracking-efficiency/Lambda/h_mass"
        if particle == "AntiLambda":
            dn = f"qa-k0s-tracking-efficiency/AntiLambda/h_mass"
    else:
        dn = f"qa-k0s-tracking-efficiency/Test/h_mass"
    print(xrange)
    print(dn)
    f.Get(dn).ls()
    h = f.Get(dn)
    h.SetDirectory(0)
    f.Close()
    if rebin > 0:
        h.Rebin(rebin)
    h.SetBit(TH1.kNoStats)
    h.GetYaxis().SetTitle(
        f"Counts per {h.GetXaxis().GetBinWidth(1)*1000.0:.1f} MeV/#it{{c}}^{{2}}")
    h.SetBit(TH1.kNoTitle)
    h.SetMarkerStyle(20)
    h.SetMarkerSize(1.3)
    h.SetMarkerColor(1)
    h.SetLineColor(1)
    h.GetXaxis().SetRangeUser(*xrange)
    can = draw_nice_canvas("V0s", logx=False, logz=True)
    h.Draw("PE")
    fsig = TF1("fsig", "gaus", *xrange)
    fbkg = TF1("fbkg", "pol2", *xrange)
    fbkg.SetLineColor(1)
    fbkg.SetLineStyle(2)
    fsum = TF1("fsum", "gaus(0)+pol2(3)", *xrange)
    h.Fit(fsig, "QNR", "", *fitrange)
    for i in range(fsig.GetNpar()):
        fsum.SetParameter(i, fsig.GetParameter(i))
    h.Fit(fsum, "QNR", "", *xrange)
    for i in range(fsig.GetNpar()):
        fsig.SetParameter(i, fsum.GetParameter(i))
    for i in range(fbkg.GetNpar()):
        fbkg.SetParameter(i, fsum.GetParameter(i+fsig.GetNpar()))
    fsum.Draw("same")
    fbkg.Draw("same")
    k0mass = 0.497614
    lambdamass = 1.115683
    if particle in ["Lambda", "AntiLambda"]:
        line = TLine(lambdamass, 0, lambdamass, h.GetMaximum())
    else:
        line = TLine(k0mass, 0, k0mass, h.GetMaximum())
    line.SetLineStyle(2)
    line.Draw()

    draw_nice_label("ALICE Performance", 0.2, 0.85, s=0.04)
    if particle == "Lambda":
        draw_nice_label("#Lambda", 0.92, 0.92, s=0.05, align=33)
    elif particle == "AntiLambda":
        draw_nice_label("#bar{#Lambda}", 0.92, 0.92, s=0.05, align=33)
    else:
        draw_nice_label("K^{0}_{s}", 0.92, 0.92, s=0.05, align=33)
    for i in enumerate([tag, "Gaussian fit:",
                        f"#mu = {fsum.GetParameter(1)*1000.0:.3f} #pm {fsum.GetParError(1)*1000.0:.3f} MeV/#it{{c}}^{{2}}",
                        f"#sigma = {fsum.GetParameter(2)*1000.0:.3f} #pm {fsum.GetParError(2)*1000.0:.3f} MeV/#it{{c}}^{{2}}"]):
        draw_nice_label(i[1], 0.2, 0.8 - 0.04*i[0])
    gPad.Modified()
    gPad.Update()
    input("Press enter to continue")
    can.SaveAs(f"/tmp/v0s{particle}.png")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fname", help="Input file")
    parser.add_argument("--charge", default="Pos", help="Particle charge")
    parser.add_argument("--particle", default="K0s", choices=["K0s", "Lambda", "AntiLambda"], help="Particle type")
    args = parser.parse_args()

    main(args.fname, particle=args.particle)
    # main(args.fname, args.charge, args.part)
