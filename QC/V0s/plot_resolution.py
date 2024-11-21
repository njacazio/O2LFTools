#!/usr/bin/env python3

from ROOT import gMinuit, TFile, TGraphErrors, TF1, TColor, TLegend
import ROOT

from sys import argv
import sys
if 1:
    sys.path.append('../../PerformancePlots/')
    from utils import draw_nice_canvas, draw_nice_frame, draw_nice_label, transpose_th2, getfromfile, update_all_canvases
from numpy import sqrt


def process_one_file(filename,
                     tag=None,
                     extralabel=None,
                     save=True):
    print("processing file", filename,
          "tag", tag,
          "extralabel", extralabel)
    # Normalization
    normalization = getfromfile(filename, "event-selection-task/hColCounterAcc").GetEntries()
    if extralabel is not None:
        normalization = getfromfile(filename, f"perf-k0s-resolution{extralabel}/K0sResolution/h1_stats").GetEntries()
    else:
        normalization = getfromfile(filename, "perf-k0s-resolution/K0sResolution/h1_stats").GetEntries()
    histograms = {}
    if "NOTRD" in filename:
        # histograms["perf-k0s-resolution/thn_mass"] = None
        histograms["perf-k0s-resolution/h2_masspT"] = None
        extralabel = "_noTRD"
    else:
        histograms["perf-k0s-resolution/h2_masspT"] = None
    alternatives = {}
    alternatives["perf-k0s-resolution/h2_masspT"] = ["perf-k0s-resolution/K0sResolution/h2_masspT"]
    if extralabel is not None:
        alternatives[f"perf-k0s-resolution{extralabel}/h2_masspT"] = [f"perf-k0s-resolution{extralabel}/K0sResolution/h2_masspT"]
    alternatives["perf-k0s-resolution_yesTOF/h2_masspT"] = ["perf-k0s-resolution_yesTOF/K0sResolution/h2_masspT"]
    alternatives["perf-k0s-resolution_noTOF/h2_masspT"] = ["perf-k0s-resolution_noTOF/K0sResolution/h2_masspT"]
    alternatives["perf-k0s-resolution_noTRD/h2_masspT"] = ["perf-k0s-resolution_noTRD/K0sResolution/h2_masspT"]
    alternatives["perf-k0s-resolution_noTRD/thn_mass"] = ["perf-k0s-resolution_noTRD/K0sResolution/thn_mass"]
    # histograms["perf-k0s-resolution/thn_mass"] = None
    # histograms["perf-k0s-resolution/h2_masseta"] = None
    # histograms["perf-k0s-resolution/h2_massphi"] = None
    # histograms["qa-k0s-tracking-efficiency/VsRadius/h_mass"] = None
    x_variables = {"perf-k0s-resolution/h2_masspT": "p_{T} (GeV/c)"}
    x_variables["perf-k0s-resolution/h2_masseta"] = "#eta"
    x_variables["perf-k0s-resolution/h2_massphi"] = "#varphi (rad)"
    for i in histograms:
        hname = i
        if extralabel is not None:
            hname = hname.replace("/", extralabel+"/")
        histograms[i] = getfromfile(filename, hname, alternatives=alternatives.get(hname, None))
        if not histograms[i]:
            print("Did not find", hname, "in", filename)
            continue
        if "THnSparseT" in histograms[i].ClassName():
            for j in range(0, histograms[i].GetNdimensions()):
                print(j, histograms[i].GetAxis(j).GetTitle(),
                      histograms[i].GetAxis(j).GetNbins(),
                      histograms[i].GetAxis(j).GetBinLowEdge(1),
                      histograms[i].GetAxis(j).GetBinUpEdge(histograms[i].GetAxis(j).GetNbins()))
            histograms[i].GetAxis(4).SetRange(1, 1)
            histograms[i].GetAxis(5).SetRange(1, 1)
            histograms[i] = histograms[i].Projection(1, 0)
            histograms[i].SetDirectory(0)
            continue
        histograms[i].SetDirectory(0)
        print(hname, histograms[i].GetXaxis().GetTitle(), histograms[i].GetXaxis().GetNbins(),
              histograms[i].GetYaxis().GetTitle(), histograms[i].GetYaxis().GetNbins())
    replacements = {"perf-k0s-resolution/h2_masspT": "perf-k0s-resolution/thn_mass"}
    for i in replacements:
        if replacements[i] not in histograms:
            continue
        histograms[i] = histograms[replacements[i]]
        histograms.pop(replacements[i])

    toremove = []
    for i in histograms:
        if not histograms[i]:
            toremove.append(i)
            continue
    for i in toremove:
        histograms.pop(i)

    graphs = {}
    to_transpose = ["qa-k0s-tracking-efficiency/VsRadius/h_mass"]
    for i in to_transpose:
        if i not in histograms:
            continue
        histograms[i] = transpose_th2(histograms[i])

    for i in histograms:
        can = draw_nice_canvas(i, replace=False)
        h = histograms[i]
        axis_title = h.GetXaxis().GetTitle().replace("(", "> (")

        g_mean = TGraphErrors()
        g_mean.SetName("g_mean"+i)
        g_mean.GetYaxis().SetTitle("#mu <" + axis_title)

        g_sigma = TGraphErrors()
        g_sigma.SetName("g_sigma"+i)
        g_sigma.GetYaxis().SetTitle("#sigma <" + axis_title)

        g_yield = TGraphErrors()
        g_yield.SetName("g_yield"+i)
        g_yield.GetYaxis().SetTitle("Yield / event")

        for g in [g_mean, g_sigma, g_yield]:
            g.GetXaxis().SetTitle(h.GetYaxis().GetTitle())
            if tag is not None:
                g.SetTitle(tag)

        h.Draw("colz")
        can.Modified()
        can.Update()
        # fun = TF1("gaus(0)+pol0(3)", "gaus(0)+pol1(3)", 0.45, 0.55)
        fun = TF1("gaus(0)+pol1(3)", "gaus(0)+pol1(3)", 0.42, 0.58)
        fun.SetParameter(0, 1.1)
        fun.SetParLimits(0, 1, 10000000)
        fun.SetParLimits(2, 0, 0.2)
        canbin = draw_nice_canvas("singlebin", replace=False)
        for k in range(1, h.GetNbinsY()+1):
            hp = h.ProjectionX("hp", k, k)
            mass_start = 0.5
            # if hp.GetMean() > 0:
            #     mass_start = hp.GetMean()
            fun.SetParameters(100, mass_start, 0.001, 0.1, 0.)
            ROOT.Math.MinimizerOptions().SetStrategy(0)
            # if k != h.GetYaxis().FindBin(1):
            #     continue
            hp.Fit(fun, "QNWW", "", 0.48, 0.52)

            def run_fit(strategy):
                ROOT.Math.MinimizerOptions().SetStrategy(strategy)
                r = hp.Fit(fun, "QINSWW")
                if not gMinuit:
                    return None
                st = gMinuit.fCstatu
                if "CONVERGED" not in st:
                    print("Fit in pT", "with strategy", strategy, "did not converge -> ", st)
                    return None
                return r
            if 1:
                for s in range(0, 4):
                    r = run_fit(s)
                if r is None:
                    r = run_fit(3)
            # print("Fit in pT at", h.GetYaxis().GetBinCenter(k), fun.GetParameter(1), fun.GetParError(1))
            canbin.cd()
            hp.Draw()
            fun.Draw("same")
            canbin.Modified()
            canbin.Update()
            if fun.GetParError(1)/fun.GetParameter(1) < 0.1:
                g_mean.SetPoint(g_mean.GetN(), h.GetYaxis().GetBinCenter(k), fun.GetParameter(1))
                g_mean.SetPointError(g_mean.GetN()-1, 0, fun.GetParError(1))
            if fun.GetParError(2)/fun.GetParameter(2) < 0.1:
                g_sigma.SetPoint(g_sigma.GetN(), h.GetYaxis().GetBinCenter(k), fun.GetParameter(2))
                g_sigma.SetPointError(g_sigma.GetN()-1, 0, fun.GetParError(2))

            fun_sig = TF1("fun_sig", "gaus(0)", 0.45, 0.55)
            fun_sig.SetParameters(fun.GetParameter(0), fun.GetParameter(1), fun.GetParameter(2))
            Y = fun_sig.Integral(0.45, 0.55)/hp.GetBinWidth(1)
            g_yield.SetPoint(g_yield.GetN(), h.GetYaxis().GetBinCenter(k), Y/normalization)
            g_yield.SetPointError(g_yield.GetN()-1, 0, sqrt(Y)/normalization)

        can = draw_nice_canvas(i+"vs", replace=False)
        draw_nice_frame(can,
                        [h.GetYaxis().GetBinLowEdge(1), h.GetYaxis().GetBinUpEdge(h.GetNbinsY()+1)],
                        [h.GetXaxis().GetBinLowEdge(1), h.GetXaxis().GetBinUpEdge(h.GetNbinsX()+1)],
                        g_mean.GetXaxis().GetTitle(),
                        g_mean.GetYaxis().GetTitle())
        g_mean.Draw("sameLP")
        graphs[i+"mean"] = g_mean
        graphs[i+"sigma"] = g_sigma
        graphs[i+"yield"] = g_yield
        can.Modified()
        can.Update()
        can = draw_nice_canvas(i+"vsSigma", replace=False)
        g_sigma.Draw("ALP")
        if save:
            out_filename = filename.replace("/", "_").replace(".root", "_"+i.replace("/", "_")).strip("_")
            out_filename = "/tmp/"+out_filename
            if extralabel is not None:
                out_filename = out_filename+extralabel
            g_mean.Clone("mean").SaveAs(out_filename+"mean.root")
            g_sigma.Clone("sigma").SaveAs(out_filename+"sigma.root")
            g_yield.Clone("yield").SaveAs(out_filename+"yield.root")
    return graphs


def main(filenames,
         save_path=None,
         extra_label=None,
         tags={"150658": "LHC15o",
               "150796": "LHC23k6c_pass1",
               "150642": "LHC23_PbPb_pass1_sampling",
               "151351": "LHC15n_pass5",
               "150994": "LHC23g",
               "152893": "LHC23f_pass1",
               "/tmp/AnalysisResults_apass1.root": "LHC23zzh_apass1_544124",
               "/tmp/AnalysisResults_LHC23r_536612_apass3.root": "LHC23r_536612_apass3",
               "/tmp/New.root": "LHC23k6d",
               "166673": "LHC23k6d",
               "/tmp/NOTRD.root": "LHC23k6d (no TRD)",
               "156569": "LHC23k6d",
               "156999": "LHC22o_pass5_skimmed_QC1",
               "168513": "LHC23k6_TRDfix",
               "hy_338209": "LHC23zs_pass3_covMatrix",
               "185780": "LHC23zs_pass3_covMatrix, tracking fixed",
               "hy_338195": "LHC23zs_pass3_QC1",
               "hy_351738": "LHC23zs_pass3_covMatrix_errs",
               "/tmp/AnalysisResults.root": "LHC23zs_pass3_covMatrix"},
         only={"150642": "19415",
               "150796": "asd",
               "151351": "19551",
               "152893": "asd"},
         savetag=""):
    results = []
    print(filenames)
    for i in enumerate(filenames):
        hasit = None
        for j in only:
            if j in i[1]:
                hasit = True
                break
        if hasit:
            if only[j] not in i[1]:
                continue
        t = None
        for j in tags:
            if j in i[1]:
                t = tags[j]
                break
        results.append(process_one_file(i[1], tag=t, extralabel=extra_label))
        # input("Press enter to continue...")
    legs = []
    canvases = []
    for i in results[0]:
        range_x = [0, 4]
        if "VsRadius" in i:
            range_x = [0, 50]
        range_y = [0, 0.01]
        if i.endswith("mean"):
            range_y = [0.492, 0.5]

        can = draw_nice_canvas(i.replace("/", "_"))
        canvases.append(can)
        draw_nice_frame(can,
                        range_x,
                        range_y,
                        results[0][i].GetXaxis().GetTitle(),
                        results[0][i].GetYaxis().GetTitle())
        colors = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#a65628']
        colors = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#ffff33', '#a65628', '#f781bf', '#999999']
        leg = TLegend(0.5, 0.5, 0.9, 0.9)
        legs.append(leg)
        for j in enumerate(results):
            if i not in j[1]:
                continue
            col = colors.pop(0)
            col = TColor.GetColor(col)
            j[1][i].Draw("LPsame")
            j[1][i].SetLineWidth(2)
            j[1][i].SetLineColor(col)
            j[1][i].SetMarkerColor(col)
            leg.AddEntry(j[1][i])
            print(j[1][i].GetTitle())
        leg.Draw()
        can.Modified()
        can.Update()

        if 0:  # Ratios!
            can_ratio = draw_nice_canvas(i+"_ratio")
            draw_nice_frame(can_ratio,
                            range_x,
                            [0, 2],
                            results[0][i].GetXaxis().GetTitle(),
                            results[0][i].GetYaxis().GetTitle() + " ratio to " + results[0][i].GetTitle())

            for j in enumerate(results):
                if i not in j[1]:
                    continue
                # if j[0] == 0:
                #     continue
                ratio = TGraphErrors()
                ratio.SetName("Ratio_"+i)
                num = j[1][i]
                ratio.SetTitle(num.GetTitle())
                ratio.SetMarkerStyle(num.GetMarkerStyle())
                ratio.SetMarkerSize(num.GetMarkerSize())
                ratio.SetMarkerColor(num.GetMarkerColor())
                ratio.SetLineColor(num.GetLineColor())
                for k in range(num.GetN()):
                    x = num.GetPointX(k)
                    y = num.GetPointY(k)
                    yd = results[0][i].Eval(x)
                    if yd > 0:
                        ratio.AddPoint(x, y/yd)
                ratio.Draw("LPsame")
            leg.Draw()
            can_ratio.Modified()
            can_ratio.Update()
        # input("Press enter to continue...")
    update_all_canvases()

    if save_path is not None:
        for i in canvases:
            outname = save_path+"/"+i.GetName()
            if extra_label is not None:
                outname += extra_label
            i.SaveAs(outname+savetag+".root")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Plot resolution')
    parser.add_argument('filenames', metavar='N', type=str, nargs='+',
                        help='Files to process')
    parser.add_argument('--save_path', "-s", type=str, default=None,
                        help='Save as')
    parser.add_argument('--extralabel', "-e", type=str, default=None,
                        help='Extra label')
    parser.add_argument('--savetag', "-S", type=str, default="",
                        help='Save tag')
    parser.add_argument("--background", "-b", action="store_true")
    args = parser.parse_args()
    from ROOT import gROOT
    if args.background:
        gROOT.SetBatch(True)
    main(filenames=args.filenames,
         extra_label=args.extralabel,
         save_path=args.save_path,
         savetag=args.savetag)
