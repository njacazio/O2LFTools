#!/usr/bin/env python3

"""
Script to plot the V0 performance plots
"""

from ROOT import TFile, gPad, TH1, TLine, TF1, TLegend, gROOT, gInterpreter, TH1F
from utils import draw_nice_canvas, draw_nice_label, draw_nice_frame
from logmaker import *


def main(fname,
         rebin=-1,
         tag="LHC22f",
         particle="K0s",
         show_fit_range=False,
         show_intermediate_steps=True,
         bkg_function="pol2",
         use_qa_output=False,
         x_projection_range=None,
         xrange=None,
         yrange=None,
         show_mass_line=True,
         normalize="events",
         show_sum_function=False,
         show_gaussian_parameters=False,
         label="",
         y_parameter_label=0.5,
         scale_y_range=1.1):
    f = TFile(fname, "READ")
    # f.ls()
    if xrange is None:
        xrange = {"K0s": [0.41, 0.60],
                  #   "Lambda": [1.1, 1.13],
                  "D0": [1.72, 2.0],
                  "Lambda": [1.08, 1.2],
                  "AntiLambda": [1.1, 1.13],
                  "XiPlus": [1.29, 1.35],
                  "XiMinus": [1.29, 1.35],
                  "OmegaMinus": [1.63, 1.71],
                  "OmegaPlus": [1.63, 1.71]}
    showrange = {"Lambda": [1.1, 1.13]}
    fitrange = {"K0s": [0.48, 0.52],
                # "Lambda": [0.9, 1.5],
                "D0": xrange["D0"],
                "Lambda": [1.1, 1.14],
                "AntiLambda": [1.1, 1.14],
                "XiPlus": [1.31, 1.33],
                "XiMinus": [1.31, 1.33],
                "OmegaMinus": [1.66, 1.68],
                "OmegaPlus": [1.66, 1.68]}
    if type(fitrange) is dict:
        xrange = xrange[particle]
    fitrange = fitrange[particle]
    dn = {"K0s": "lambdakzero-analysis/h3dMassK0Short",
          "Lambda": "lambdakzero-analysis/h3dMassLambda",
          "D0": "cout",
          "AntiLambda": "lambdakzero-analysis/h3dMassAntiLambda",
          "XiPlus": "cascade-analysis/h2dMassXiPlus",
          "XiMinus": "cascade-analysis/h2dMassXiMinus",
          "OmegaMinus": "cascade-analysis/h2dMassOmegaMinus",
          "OmegaPlus": "cascade-analysis/h2dMassOmegaPlus"}
    if use_qa_output:
        dn = {"K0s": "lambdakzero-qa/hMassK0Short",
              "Lambda": "lambdakzero-qa/hMassLambda",
              "AntiLambda": "lambdakzero-qa/hMassAntiLambda",
              "XiPlus": "cascade-qa/h2dMassXiPlus",
              "XiMinus": "cascade-qa/h2dMassXiMinus",
              "OmegaMinus": "cascade-qa/h2dMassOmegaMinus",
              "OmegaPlus": "cascade-qa/h2dMassOmegaPlus"}
        if not f.Get(dn[particle]):
            print("+++", dn[particle], "is not there")
            dn[particle] = f"v0cascades-q-a/histos-V0/InvMass{particle}"
            if "Xi" in particle or "Omega" in particle:
                dn[particle] = f"v0cascades-q-a/histos-Casc/InvMass{particle}"
            print("+++ Retrying with", dn[particle])
        if not f.Get(dn[particle]):
            print("+++", dn[particle], "is not there")
            dn[particle] = f"qa-cascades/mass{particle}"
            if "Xi" in particle or "Omega" in particle:
                dn[particle] = f"qa-cascades/massXi"
            print("+++ Retrying with", dn[particle])
    dn = dn[particle]
    particle_mass = {"K0s": 0.497614,
                     "D0": 1.86484,
                     "Lambda": 1.115683, "AntiLambda": 1.115683,
                     "XiPlus": 1.32171, "XiMinus": 1.32171,
                     "OmegaPlus": 1.672, "OmegaMinus": 1.672}[particle]
    print("X range:", xrange)
    print("using histogram", dn)
    h = None
    if not f.Get(dn):
        f.ls()
        raise ValueError("Did not find" + dn)
    if "TCanvas" in f.Get(dn).ClassName():
        f.Get(dn).Draw()
        gPad.Modified()
        gPad.Update()
        input("Press enter to continue")
        for i in f.Get(dn).GetListOfPrimitives():
            if "TH1" in i.ClassName():
                h = TH1F("asd", "asd,", i.GetNbinsX(), i.GetXaxis().GetBinLowEdge(1), i.GetXaxis().GetBinUpEdge(i.GetNbinsX()))
                for j in range(1, i.GetNbinsX() + 1):
                    h.SetBinContent(j, i.GetBinContent(j))
                break
    maind = "/".join(dn.split("/")[:-1])
    # f.Get(maind).ls()
    hev = f.Get(f"{maind}/hEventSelection")
    hev = f.Get(f"event-selection-task/hColCounterAcc")
    nevents = 1
    if hev:
        if hev.GetXaxis().GetBinLabel(1) != "":
            nevents = int(hev.GetEntries())
        else:
            nevents = int(hev.GetBinContent(hev.GetNbinsX()))
        print(nevents, "events", hev.GetXaxis().GetBinLabel(hev.GetNbinsX()))
    f.Get(dn).ls()
    if not h:
        h = f.Get(dn)
    h.SetDirectory(0)
    f.Close()
    print("Got", h.ClassName(), h.GetName())
    if "TH2" in h.ClassName():
        draw_nice_canvas("2d")
        h.DrawCopy("colz")
        gPad.Modified()
        gPad.Update()
        if x_projection_range is not None:
            print("Doing projection in", x_projection_range)
            x_bin = [h.GetXaxis().FindBin(x_projection_range[0]),
                     h.GetXaxis().FindBin(x_projection_range[1])]
            x_projection_range = [h.GetXaxis().GetBinLowEdge(x_bin[0]),
                                  h.GetXaxis().GetBinUpEdge(x_bin[1])]
            h = h.ProjectionY(h.GetName(), *x_bin)
            x_projection_range = f"{x_projection_range[0]:.2f} "+"< #it{p}_{T} <"+f" {x_projection_range[1]:.2f} "+"GeV/#it{c}"
            print("Using x projection range", x_projection_range, "in", h.GetXaxis().GetTitle())
        else:
            h = h.ProjectionY()
        h.SetDirectory(0)
    if "TH3" in h.ClassName():
        if x_projection_range is not None:
            h.GetYaxis().SetRangeUser(*x_projection_range)
            x_projection_range = f"{int(x_projection_range[0])} "+"< #it{p}_{T} <"+f" {int(x_projection_range[1])} "+"GeV/#it{c}"
            print("Using x projection range", x_projection_range, "in", h.GetYaxis().GetTitle())
        print("X", h.GetXaxis().GetTitle(), h.GetXaxis().GetXmin(), h.GetXaxis().GetXmax())
        print("Y", h.GetYaxis().GetTitle(), h.GetYaxis().GetXmin(), h.GetYaxis().GetXmax())
        print("Z", h.GetZaxis().GetTitle(), h.GetZaxis().GetXmin(), h.GetZaxis().GetXmax())
        draw_nice_canvas("3d")
        h.DrawCopy()
        gPad.Modified()
        gPad.Update()
        draw_nice_canvas("2d")
        h.Project3D("zy").DrawCopy("colz")
        gPad.Modified()
        gPad.Update()
        h = h.Project3D("z")
    if rebin > 0:
        h.Rebin(rebin)
    h.SetBit(TH1.kNoStats)
    if normalize.lower() == "integral":
        h.GetYaxis().SetTitle(f"Normalized counts per {h.GetXaxis().GetBinWidth(1)*1000.0:.1f} MeV/#it{{c}}^{{2}}")
    elif normalize.lower() == "events":
        h.GetYaxis().SetTitle(f"1/N_{{ev}} counts per {h.GetXaxis().GetBinWidth(1)*1000.0:.1f} MeV/#it{{c}}^{{2}}")
        h.Scale(1.0/nevents)
    else:
        h.GetYaxis().SetTitle(f"Counts per {h.GetXaxis().GetBinWidth(1)*1000.0:.1f} MeV/#it{{c}}^{{2}}")
    h.SetBit(TH1.kNoTitle)
    h.SetMarkerStyle(20)
    h.SetMarkerSize(1.3)
    h.SetMarkerColor(1)
    h.SetLineColor(1)
    h.GetXaxis().SetTitle("#it{m} (GeV/#it{c}^{2})")
    h.GetXaxis().SetRangeUser(*xrange)
    if normalize.lower() == "integral":
        print("Normalizing to integral")
        if h.Integral() > 0:
            h.Scale(1.0/h.Integral(h.GetXaxis().FindBin(xrange[0]),
                                   h.GetXaxis().FindBin(xrange[1])))
        else:
            print("Warning: Integral is 0. Cannot scale", h.GetName(), "has", h.GetEntries(), "entries")
    h.GetXaxis().SetRangeUser(*xrange)
    h.SetMinimum(0)
    h.SetMaximum((h.GetMaximum()+h.GetBinError(h.GetMaximumBin()))*scale_y_range)
    if yrange is not None:
        h.SetMaximum(yrange)
    can = draw_nice_canvas("V0s"+particle, logx=False, logz=True)
    if showrange.setdefault(particle, False):
        draw_nice_frame(can, showrange[particle], h, h, h)
    else:
        draw_nice_frame(can, xrange, h, h, h)
    h.Draw("PESAME")
    # Functions
    sig_function = "[0]*(TMath::Gaus(x, [1], [2], true) + TMath::Gaus(x, [1], [3], true))"  # Multiple gaussian
    sig_function = "[0]*(TMath::Gaus(x, [1], [2], true))"
    fsig = TF1("fsig", f"{sig_function}", *xrange)
    print("Signal function: ", fsig.GetExpFormula())
    fsig.SetParName(0, "Norm")
    fsig.SetLineColor(5)
    fsig.SetParameter(0, 0.5)
    fsig.SetParLimits(0, 0, 1)
    fsig.SetParameter(1, particle_mass)
    fsig.SetParLimits(1, particle_mass-0.1, particle_mass+0.1)
    fsig.SetParameter(2, 0.005)
    fsig.SetParLimits(2, 0.001, 0.01)
    fsig.SetParameter(3, 0.006)
    fsig.SetParLimits(3, 0.001, 0.01)
    fsig_simple_bkg = sig_function
    if ")" not in sig_function:
        fsig_simple_bkg = f"{fsig_simple_bkg}(0)"
    fsig_simple_bkg += f"+pol0({fsig.GetNpar()})"
    fsig_simple_bkg = TF1("fsig_simple_bkg", fsig_simple_bkg, *xrange)
    fsig_simple_bkg.SetParLimits(fsig.GetNpar(), 0, 1000)
    print("Signal with simple background function: ", fsig_simple_bkg.GetExpFormula())
    fsig_simple_bkg.SetLineColor(3)
    fsig_simple_bkg.SetLineStyle(2)
    fbkg = TF1("fbkg", f"{bkg_function}", *xrange)
    print("Background function: ", fbkg.GetExpFormula())
    fbkg.SetLineColor(1)
    fbkg.SetLineStyle(2)
    fsum = sig_function
    if ")" not in sig_function:
        fsum = f"{fsum}(0)"
    fsum += f"+{bkg_function}({fsig.GetNpar()})"
    fsum = TF1("fsum", fsum, *xrange)
    print("Sum function: ", fsum.GetExpFormula())
    leg = TLegend(0.19, 0.58, 0.35, 0.66)
    leg.SetTextSize(0.025)
    leg.SetBorderSize(0)
    leg.SetLineColor(0)
    # leg.SetFillColor(2)
    if show_sum_function:
        leg.AddEntry(fsum, "Gaussian fit + pol. bkg.", "l")
    leg.AddEntry(fbkg, "pol. bkg.", "l")

    optfit = "NL"
    if show_intermediate_steps:
        optfit = "+"
    h.Fit(fsig, optfit, "", *fitrange)  # Fitting with signal only

    for i in range(fsig.GetNpar()):
        fsig_simple_bkg.SetParName(i, fsig.GetParName(i))
        fsig_simple_bkg.SetParameter(i, fsig.GetParameter(i))
        fsig_simple_bkg.SetParError(i, fsig.GetParError(i))

    fit_range_simple_bkg = fitrange
    if "D0" in particle:
        fit_range_simple_bkg = [fsig_simple_bkg.GetParameter(1) - 3 * fsig_simple_bkg.GetParameter(2),
                                fsig_simple_bkg.GetParameter(1) + 3 * fsig_simple_bkg.GetParameter(2)]
    h.Fit(fsig_simple_bkg, optfit, "", *fit_range_simple_bkg)  # Fitting with simple background

    for i in range(fsig.GetNpar()):
        print("Setting", fsum.GetParName(i), "to", fsig.GetParameter(i))
        fsum.SetParName(i, fsig.GetParName(i))
        fsum.SetParameter(i, fsig_simple_bkg.GetParameter(i))
        if "Norm" not in fsig.GetParName(i) or 1:
            delta = 10 * fsig_simple_bkg.GetParError(i)
            delta = 2 * fsig_simple_bkg.GetParError(i)
            limits = [fsig_simple_bkg.GetParameter(i) - delta,
                      fsig_simple_bkg.GetParameter(i) + delta]
            print(fsum.GetParName(i), limits)
            fsum.SetParLimits(i, *limits)
    h.Fit(fsum, "NWW", "", *xrange)
    for i in range(fsig.GetNpar()):
        fsig.SetParameter(i, fsum.GetParameter(i))
    for i in range(fbkg.GetNpar()):
        print("Setting for bkg", i, fbkg.GetParName(i), "to", fsum.GetParameter(i + fsig.GetNpar()))
        fbkg.SetParameter(i, fsum.GetParameter(i + fsig.GetNpar()))
    print("Value of background at", particle_mass, "is", fbkg.Eval(particle_mass))
    if show_sum_function:
        fsum.Draw("same")
    fbkg.Draw("same")
    leg.Draw()
    lines = []
    if show_mass_line:
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
    decay_channels = {"K0s": "K^{0}_{S} #rightarrow #pi^{+}#pi^{#minus }",
                      "D0": "D^{0} #rightarrow K^{-}#pi^{+} and charge conjugate",
                      "Lambda": "#Lambda #rightarrow p#pi^{#minus }",
                      "AntiLambda": "#bar{#Lambda} #rightarrow #bar{p}#pi^{+}",
                      "XiPlus": "#Xi^{+} #rightarrow #bar{#Lambda}#pi^{+} #rightarrow #bar{p}#pi^{+}#pi^{+}",
                      "XiMinus": "#Xi^{#minus} #rightarrow #Lambda#pi^{#minus } #rightarrow p#pi^{#minus }#pi^{#minus }",
                      "OmegaMinus": "#Omega^{#minus} #rightarrow #Lambda K^{#minus} #rightarrow p#pi^{#minus }K^{#minus}",
                      "OmegaPlus": "#bar{#Omega}^{+} #rightarrow #bar{#Lambda} K^{+} #rightarrow #bar{p}#pi^{+}K^{+}"}

    to_write = ["Run 3, pp #sqrt{#it{s}} = 13.6 TeV"]
    to_write = ["Run 3, Pb#minusPb #sqrt{#it{s}_{NN}} = 5.36 TeV LHC22k3"]
    to_write = ["Run 3, Pb#minusPb #sqrt{#it{s}_{NN}} = 5.36 TeV LHC22s pass3"]
    to_write = ["Run 3, Pb#minusPb #sqrt{#it{s}_{NN}} = 5.36 TeV"]
    to_write = ["Run 3, pp #sqrt{#it{s}} = 13.6 TeV LHC22m pass2"]
    to_write = [label]
    if type(x_projection_range) is str:
        to_write.append(x_projection_range)
    else:
        if "D0" in particle:
            to_write.append("1 < #it{p}_{T} < 36 GeV/#it{c}")
        else:
            to_write.append("0 < #it{p}_{T} < 10 GeV/#it{c}")
    to_write.append("|#it{y}| < 0.5")
    to_write.append(decay_channels[particle])
    if normalize == "events":
        to_write.append(f"N_{{ev}} = {int(nevents)}")

    for i in enumerate(to_write):
        draw_nice_label(i[1], label_x, label_y-0.044*(i[0]+1)-0.01, s=0.033)
    particle_symbol = {"Lambda": "#Lambda",
                       "D0": "D^{0}",
                       "AntiLambda": "#bar{#Lambda}",
                       "K0s": "K^{0}_{S}",
                       "XiPlus": "#Xi^{+}",
                       "XiMinus": "#Xi^{#minus}",
                       "OmegaPlus": "#bar{#Omega}^{+}",
                       "OmegaMinus": "#Omega^{#minus }"}[particle]
    if show_sum_function and show_gaussian_parameters:
        to_write = []
        to_write.append(f"Gaussian fit:")
        to_write.append(f"#mu = {fsig.GetParameter(1):.4f}")
        to_write.append(f"#sigma = {fsig.GetParameter(2):.4f}")
        for i in enumerate(to_write):
            draw_nice_label(i[1], .7, y_parameter_label-0.03*(i[0]+1)-0.01, s=0.025)

    draw_nice_label(particle_symbol, 0.92, 0.92, s=0.07, align=33)
    if 0:
        for i in enumerate([tag, "Gaussian fit:",
                            f"#mu = {fsum.GetParameter(1)*1000.0:.3f} #pm {fsum.GetParError(1)*1000.0:.3f} MeV/#it{{c}}^{{2}}",
                            f"#sigma = {fsum.GetParameter(2)*1000.0:.3f} #pm {fsum.GetParError(2)*1000.0:.3f} MeV/#it{{c}}^{{2}}"]):
            draw_nice_label(i[1], label_x, label_y - 0.04*(i[0]+1), s=0.03)
    gPad.Modified()
    gPad.Update()
    if not gROOT.IsBatch():
        input("Press enter to continue")
    can.SaveAs(f"/tmp/v0s{particle}.png")
    can.SaveAs(f"/tmp/v0s{particle}.pdf")
    can.SaveAs(f"/tmp/v0s{particle}.eps")


if __name__ == "__main__":
    parser = get_default_parser(description=__doc__)
    parser.add_argument("fname", help="Input file")
    parser.add_argument("--particle", default="K0s", choices=["K0s", "Lambda", "AntiLambda", "XiPlus", "XiMinus", "D0", "OmegaMinus", "OmegaPlus"],
                        nargs="+", help="Particle type")
    parser.add_argument("--bkg_function", default="pol2", help="Function to use as background")
    parser.add_argument("--rebin", type=int, default=-1, help="Times to rebin")
    parser.add_argument("--show_fit_range", action="store_true", help="Show fit range")
    parser.add_argument("--show_intermediate_steps", "--show_steps", action="store_true", help="Show intermediate steps")
    parser.add_argument("--show_mass_line", action="store_true", help="Show a line corresponding to the mass of the particle")
    parser.add_argument("--xrange", type=float, nargs=2, help="Range in invariant mass", default=None)
    parser.add_argument("--yrange", type=float, help="Range in y", default=None)
    parser.add_argument("--scale_y_range", "--y_scale", "-y", type=float, help="Scale in the range in y", default=1.1)
    parser.add_argument("--show_sum_function", "-s", action="store_true", help="Show sum function")
    parser.add_argument("--show_gaussian_parameters", "-f", action="store_true", help="Show gaussian parameters on the plot")
    parser.add_argument("--x_projection_range", "--pt", type=float, default=None, help="Projection range i.e. pT", nargs=2)
    parser.add_argument("--use_qa_output", "-q", action="store_true", help="Use qa output")
    parser.add_argument("--label", "-l", nargs="+", help="Label to write", default="Run 3, pp #sqrt{#it{s}} = 13.6 TeV LHC22m pass2")
    parser.add_argument("--normalize", "-n", help="Normalize mode", default="integral", choices=["events", "integral", "none"])
    parser.add_argument("--y_parameter_label", help="Position in y of the paremter labels", default=0.5, type=float)
    args = parse_default_args()
    if type(args.label) is list:
        args.label = " ".join(args.label).strip()
    if args.show_gaussian_parameters and not args.show_sum_function:
        raise ValueError("Cannot show gaussian parameters without showing sum function, ignoring --show_gaussian_parameters")

    if type(args.particle) == str:
        args.particle = [args.particle]
    gROOT.SetBatch(args.background)
    for i in args.particle:
        main(args.fname,
             particle=i,
             bkg_function=args.bkg_function,
             rebin=args.rebin,
             xrange=args.xrange,
             yrange=args.yrange,
             normalize=args.normalize,
             show_mass_line=args.show_mass_line,
             scale_y_range=args.scale_y_range,
             show_fit_range=args.show_fit_range,
             label=args.label,
             x_projection_range=args.x_projection_range,
             use_qa_output=args.use_qa_output,
             show_sum_function=args.show_sum_function,
             y_parameter_label=args.y_parameter_label,
             show_gaussian_parameters=args.show_gaussian_parameters,
             show_intermediate_steps=args.show_intermediate_steps)
