#!/usr/bin/env python3

"""
Script to plot the V0 performance plots
"""

from ROOT import TFile, gPad, TH1, TLine, TF1, TLegend
from utils import draw_nice_canvas, draw_nice_label, draw_nice_frame
import argparse


def main(fname, rebin=-1,
         tag="LHC22f",
         particle="K0s",
         show_fit_range=False,
         show_intermediate_steps=True,
         bkg_function="pol2",
         scale_y_range=1.1):
    f = TFile(fname, "READ")
    # f.ls()
    xrange = {"K0s": [0.43, 0.54],
              "Lambda": [1.101, 1.128],
              "AntiLambda": [1.086, 1.14],
              "XiPlus": [1.29, 1.35],
              "XiMinus": [1.29, 1.35],
              "OmegaMinus": [1.62, 1.71],
              "OmegaPlus": [1.62, 1.71]}[particle]
    fitrange = {"K0s": [0.48, 0.52],
                "Lambda": [1.1, 1.14],
                "AntiLambda": [1.1, 1.14],
                "XiPlus": [1.31, 1.33],
                "XiMinus": [1.31, 1.33],
                "OmegaMinus": [1.66, 1.68],
                "OmegaPlus": [1.66, 1.68]}[particle]
    dn = {"K0s": "qa-k0s-tracking-efficiency/Test/h_mass",
          "Lambda": "qa-k0s-tracking-efficiency/Lambda/h_mass",
          "AntiLambda": "qa-k0s-tracking-efficiency/AntiLambda/h_mass",
          "XiPlus": "cascade-analysis/h2dMassXiPlus",
          "XiMinus": "cascade-analysis/h2dMassXiPlus",
          "OmegaMinus": "cascade-analysis/h2dMassOmegaMinus",
          "OmegaPlus": "cascade-analysis/h2dMassOmegaPlus"}[particle]
    particle_mass = {"K0s": 0.497614,
                     "Lambda": 1.115683, "AntiLambda": 1.115683,
                     "XiPlus": 1.32171, "XiMinus": 1.32171,
                     "OmegaPlus": 1.672, "OmegaMinus": 1.672}[particle]
    print(xrange)
    print(dn)
    if not f.Get(dn):
        f.ls()
        input("Did not find" + dn)
    f.Get(dn).ls()
    h = f.Get(dn)
    h.SetDirectory(0)
    f.Close()
    if "TH2" in h.ClassName():
        h = h.ProjectionY()
    if rebin > 0:
        h.Rebin(rebin)
    h.SetBit(TH1.kNoStats)
    h.GetYaxis().SetTitle(f"Normalized counts per {h.GetXaxis().GetBinWidth(1)*1000.0:.1f} MeV/#it{{c}}^{{2}}")
    h.SetBit(TH1.kNoTitle)
    h.SetMarkerStyle(20)
    h.SetMarkerSize(1.3)
    h.SetMarkerColor(1)
    h.SetLineColor(1)
    h.GetXaxis().SetTitle("#it{m} (GeV/#it{c}^{2})")
    h.GetXaxis().SetRangeUser(*xrange)
    h.Scale(1.0/h.Integral())
    h.SetMaximum(h.GetMaximum()*scale_y_range)
    can = draw_nice_canvas("V0s"+particle, logx=False, logz=True)
    draw_nice_frame(can, xrange, h, h, h)
    h.Draw("PESAME")
    # Functions
    fsig = TF1("fsig", "gaus", *xrange)
    fsig.SetParameter(1, particle_mass)
    fsig.SetParLimits(1, particle_mass+0.1, particle_mass-0.1)
    fsig_simple_bkg = TF1("fsig_simple_bkg", "gaus(0)+pol0(3)", *xrange)
    fsig_simple_bkg.SetLineColor(3)
    fsig_simple_bkg.SetLineStyle(2)
    fbkg = TF1("fbkg", f"{bkg_function}", *xrange)
    fbkg.SetLineColor(1)
    fbkg.SetLineStyle(2)
    fsum = TF1("fsum", f"gaus(0)+{bkg_function}(3)", *xrange)
    leg = TLegend(0.19, 0.58, 0.35, 0.66)
    leg.SetTextSize(0.025)
    leg.SetBorderSize(0)
    leg.SetLineColor(0)
    # leg.SetFillColor(2)
    leg.AddEntry(fsum, "Gaussian fit + pol. bkg.", "l")
    leg.AddEntry(fbkg, "pol. bkg.", "l")

    h.Fit(fsig, "N", "", *fitrange)
    for i in range(fsig.GetNpar()):
        fsig_simple_bkg.SetParName(i, fsig.GetParName(i))
        fsig_simple_bkg.SetParameter(i, fsig.GetParameter(i))
        fsig_simple_bkg.SetParError(i, fsig.GetParError(i))
    h.Fit(fsig_simple_bkg, "N", "", *fitrange)
    if show_intermediate_steps:
        fsig.DrawClone("SAME")
        fsig_simple_bkg.DrawClone("SAME")

    for i in range(fsig.GetNpar()):
        fsum.SetParName(i, fsig.GetParName(i))
        fsum.SetParameter(i, fsig_simple_bkg.GetParameter(i))
        if i > 0:
            limits = [fsig_simple_bkg.GetParameter(i) - 10 * fsig_simple_bkg.GetParError(i),
                      fsig_simple_bkg.GetParameter(i) + 10 * fsig_simple_bkg.GetParError(i)]
            print(fsum.GetParName(i), limits)
            fsum.SetParLimits(i, *limits)
    h.Fit(fsum, "QNR", "", *xrange)
    for i in range(fsig.GetNpar()):
        fsig.SetParameter(i, fsum.GetParameter(i))
    for i in range(fbkg.GetNpar()):
        fbkg.SetParameter(i, fsum.GetParameter(i+fsig.GetNpar()))
    fsum.Draw("same")
    fbkg.Draw("same")
    leg.Draw()
    lines = []
    if 0:
        lines.append(TLine(particle_mass, h.GetMinimum(), particle_mass, h.GetMaximum()))
    if show_fit_range:
        lines.append(TLine(fitrange[0], h.GetMinimum(), fitrange[0], h.GetMaximum()))
        lines.append(TLine(fitrange[1], h.GetMinimum(), fitrange[1], h.GetMaximum()))
    for i in lines:
        i.SetLineStyle(2)
        i.Draw()

    label_y = 0.88
    label_x = 0.2
    draw_nice_label("ALICE Performance", label_x, label_y, s=0.04)
    decay_channels = {"K0s": "#it{K}^{0}_{S} #rightarrow #pi^{+}#pi^{#minus }",
                      "Lambda": "#Lambda #rightarrow p#pi^{#minus }",
                      "AntiLambda": "#Lambda #rightarrow #bar{p}#pi^{+}",
                      "XiPlus": "#Xi^{+} #rightarrow #bar{#Lambda}#pi^{+} #rightarrow #bar{p}#pi^{+}#pi^{+}",
                      "XiMinus": "#Xi^{#minus} #rightarrow #Lambda#pi^{#minus } #rightarrow p#pi^{#minus }#pi^{#minus }",
                      "OmegaMinus" :"",
                      "OmegaPlus": ""}
    for i in enumerate(["Run 3, pp #sqrt{#it{s}} = 13.6 TeV", "0 < #it{p}_{T} < 10 GeV/#it{c}", "|y| < 0.5", decay_channels[particle]]):
        draw_nice_label(i[1], label_x, label_y-0.044*(i[0]+1)-0.01, s=0.033)
    particle_symbol = {"Lambda": "#Lambda", "AntiLambda": "#bar{#Lambda}",
                       "K0s": "K^{0}_{S}",
                       "XiPlus": "#Xi^{+}", "XiMinus": "#Xi^{#minus}",
                       "OmegaPlus": "#bar{#Omega}^{+}", "OmegaMinus": "#Omega^{#minus }"}[particle]
    draw_nice_label(particle_symbol, 0.92, 0.92, s=0.07, align=33)
    if 0:
        for i in enumerate([tag, "Gaussian fit:",
                            f"#mu = {fsum.GetParameter(1)*1000.0:.3f} #pm {fsum.GetParError(1)*1000.0:.3f} MeV/#it{{c}}^{{2}}",
                            f"#sigma = {fsum.GetParameter(2)*1000.0:.3f} #pm {fsum.GetParError(2)*1000.0:.3f} MeV/#it{{c}}^{{2}}"]):
            draw_nice_label(i[1], label_x, label_y - 0.04*(i[0]+1), s=0.03)
    gPad.Modified()
    gPad.Update()
    input("Press enter to continue")
    can.SaveAs(f"/tmp/v0s{particle}.png")
    can.SaveAs(f"/tmp/v0s{particle}.pdf")
    can.SaveAs(f"/tmp/v0s{particle}.eps")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fname", help="Input file")
    parser.add_argument("--charge", default="Pos", help="Particle charge")
    parser.add_argument("--particle", default="K0s", choices=["K0s", "Lambda", "AntiLambda", "XiPlus", "XiMinus", "OmegaMinus", "OmegaPlus"],
                        nargs="+", help="Particle type")
    parser.add_argument("--bkg_function", default="pol2", help="Function to use as background")
    parser.add_argument("--rebin", type=int, default=-1, help="Times to rebin")
    parser.add_argument("--show_fit_range", action="store_true", help="Show fit range")
    parser.add_argument("--show_intermediate_steps", action="store_true", help="Show intermediate steps")
    args = parser.parse_args()

    if type(args.particle) == str:
        args.particle = [args.particle]
    for i in args.particle:
        main(args.fname,
             particle=i,
             bkg_function=args.bkg_function,
             rebin=args.rebin,
             show_fit_range=args.show_fit_range,
             show_intermediate_steps=args.show_intermediate_steps)
