#!/usr/bin/env python3

"""
Script to plot the TOF mass distribution
"""

from ROOT import TFile, TCanvas, TLatex, TNamed, TH1
import argparse
from utils import draw_nice_canvas, draw_nice_frame


def get_for_tofmass(filename, tag=None, subdir=None):
    f = TFile(filename, "READ")
#     f.ls()
    hn = f"tof-pid-collision-time-qa/withtof/mass"

    if subdir is not None:
        hn = f"tof-pid-collision-time-qa/{subdir}/mass"
    if not f.Get(hn):
        f.Get("tof-pid-beta-qa/event").ls()
        hn = f"tof-pid-beta-qa/event/tofmass{subdir}"
        f.ls()
    h = f.Get(hn)
    h.SetDirectory(0)
    f.Close()
    if tag is not None:
        h.GetListOfFunctions().Add(TNamed(tag, tag))
    return h


def draw_tofmass(h,
                 y_label=0.85,
                 x_label=0.53,
                 logy=True,
                 label_size=0.033,
                 x=1,
                 rebin=4,
                 xrange=[0, 3],
                 label="",
                 energylabel="Run 3, pp #sqrt{#it{s}} = 900 GeV",
                 saveas=None):

    h.SetLineWidth(2)
    if rebin > 0:
        h.Rebin(rebin)
    h.SetBit(TH1.kNoTitle)
    h.SetBit(TH1.kNoStats)

    can = draw_nice_canvas("TOFmass", logx=False, logy=True)
    y = [1, h.GetMaximum()*2]
    y = [1, h.GetMaximum()*4]
    frame = draw_nice_frame(can, xrange,
                            y, h,
                            "Counts")
    h.Draw("same")
    latex = TLatex(x_label, y_label, "ALICE O^{2}")
    latex = TLatex(x_label, y_label, "ALICE Performance")
    latex.SetTextFont(42)
    latex.SetTextSize(0.05)
    latex.SetNDC()
    latex.Draw()
    delta = 0.05
    if 1:
        y_label -= delta
        latex.DrawLatex(x_label, y_label,
                        energylabel).SetTextSize(label_size)
    if 0:
        y_label -= delta
        latex.DrawLatex(x_label, y_label,
                        "TOF performance").SetTextSize(label_size)
    if label != "":
        y_label -= delta
        latex.DrawLatex(x_label, y_label, label).SetTextSize(label_size)
    for i in h.GetListOfFunctions():
        y_label -= delta
        latex.DrawLatex(x_label, y_label, i.GetName()).SetTextSize(label_size)

    yl = y_label - delta*2
    xl = x_label*1.2
    xd = 0.05
    xs = 0.03
    masses = {"El": 0.000511, "Mu": 0.105658, "Pi": 0.139570,
              "Ka": 0.493677, "Pr": 0.938272, "De": 1.8756129,
              "Tr": 2.8089211, "Al": 3.7273794, "He": 2.8083916}
    names = {"Pi": "#pi",
             "Ka": "K", "Pr": "p", "De": "d"}
    for i in ["Pi", "Ka", "Pr", "De"]:
        x_l = masses[i]+0.02
        y_l = h.GetBinContent(h.FindBin(x_l))*1.2
        l = latex.DrawLatex(x_l+0.02, y_l, names[i])
        l.SetNDC(False)
        l.SetTextSize(0.045)

    if saveas is not None:
        if type(saveas) is not list:
            saveas = [saveas]
        for i in saveas:
            can.SaveAs(i)
    return h, latex


def main(filename, tag):
    mass = get_for_tofmass(filename, tag="apass3", subdir="EvTimeTOF")
    d = draw_tofmass(mass, saveas="/tmp/TOFMass.pdf",
                     rebin=6,
                     energylabel="Run 3, pp #sqrt{#it{s}} = 13.6 TeV")
    input("Press Enter to continue...")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", "-v",
                        action="store_true", help="Verbose mode.")
    parser.add_argument("-b",
                        action="store_true", help="Background mode.")
    parser.add_argument("data_file", type=str,
                        help="Input file for the data")
    parser.add_argument("--tag", type=str, default="",
                        help="Input tag for the data")
    parser.add_argument("--particles", "-p", type=str, nargs="+", default=["Pi"],
                        help="Particle type.")
    parser.add_argument("--charges", "-c", type=str, nargs="+", default=["Pos"],
                        help="Particle charge.")

    args = parser.parse_args()
    main(args.data_file, args.tag)
