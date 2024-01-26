#!/usr/bin/env python3

from ROOT import gMinuit, TFile, TGraphErrors, TF1, TColor, TLegend
import ROOT

from sys import argv
import sys
if 1:
    sys.path.append('../../PerformancePlots/')
    from utils import draw_nice_canvas, draw_nice_frame, draw_nice_label, transpose_th2


def process_one_file(filename, tag=None):
    file = TFile(filename, "READ")
    histograms = {}
    histograms["perf-k0s-resolution/h2_masspT"] = None
    # histograms["perf-k0s-resolution/h2_masseta"] = None
    # histograms["perf-k0s-resolution/h2_massphi"] = None
    # histograms["qa-k0s-tracking-efficiency/VsRadius/h_mass"] = None
    x_variables = {"perf-k0s-resolution/h2_masspT": "p_{T} (GeV/c)"}
    x_variables["perf-k0s-resolution/h2_masseta"] = "#eta"
    x_variables["perf-k0s-resolution/h2_massphi"] = "#varphi (rad)"
    for i in histograms:
        histograms[i] = file.Get(i)
        if not histograms[i]:
            print("Did not find", i, "in", filename)
            continue
        histograms[i].SetDirectory(0)
        print(i, histograms[i].GetXaxis().GetTitle(), histograms[i].GetXaxis().GetNbins(),
              histograms[i].GetYaxis().GetTitle(), histograms[i].GetYaxis().GetNbins())
    file.Close()
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
        g_mean = TGraphErrors()
        if tag is not None:
            g_mean.SetTitle(tag)
        g_mean.GetXaxis().SetTitle(h.GetYaxis().GetTitle())
        g_mean.GetYaxis().SetTitle("#mu <" + h.GetXaxis().GetTitle().replace("(", "> ("))

        g_sigma = TGraphErrors()
        if tag is not None:
            g_sigma.SetTitle(tag)
        g_sigma.GetXaxis().SetTitle(h.GetYaxis().GetTitle())
        g_sigma.GetYaxis().SetTitle("#sigma <" + h.GetXaxis().GetTitle().replace("(", "> ("))

        h.Draw("colz")
        can.Modified()
        can.Update()
        fun = TF1("gaus(0)+pol0(3)", "gaus(0)+pol1(3)", 0.45, 0.55)
        fun.SetParLimits(0, 1, 10000000)
        fun.SetParLimits(2, 0, 0.2)
        canbin = draw_nice_canvas("singlebin", replace=False)
        for k in range(1, h.GetNbinsY()+1):
            hp = h.ProjectionX("hp", k, k)
            fun.SetParameters(1, 0.5, 0.01, 0.1, 0.)
            hp.Fit(fun, "QNRWW")

            def run_fit(strategy):
                ROOT.Math.MinimizerOptions().SetStrategy(strategy)
                r = hp.Fit(fun, "QINSWW")
                st = gMinuit.fCstatu
                if "CONVERGED" not in st:
                    print("Fit in pT", "with strategy", strategy, "did not converge -> ", st)
                    return None
                return r
            for s in range(0, 4):
                r = run_fit(s)
            if r is None:
                r = run_fit(3)
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

        can = draw_nice_canvas(i+"vs", replace=False)
        draw_nice_frame(can,
                        [h.GetYaxis().GetBinLowEdge(1), h.GetYaxis().GetBinUpEdge(h.GetNbinsY()+1)],
                        [h.GetXaxis().GetBinLowEdge(1), h.GetXaxis().GetBinUpEdge(h.GetNbinsX()+1)],
                        g_mean.GetXaxis().GetTitle(),
                        g_mean.GetYaxis().GetTitle())
        g_mean.Draw("sameLP")
        graphs[i+"mean"] = g_mean
        graphs[i+"sigma"] = g_sigma
        can.Modified()
        can.Update()
        can = draw_nice_canvas(i+"vsSigma", replace=False)
        g_sigma.Draw("ALP")
    return graphs


def main(filenames,
         tags={"150658": "LHC15o",
               "150796": "LHC23k6c_pass1",
               "150642": "LHC23_PbPb_pass1_sampling",
               "151351": "LHC15n_pass5",
               "150994": "LHC23g",
               "152893": "LHC23f_pass1",
               "/tmp/AnalysisResults_apass1.root": "LHC23zzh_apass1_544124",
               "/tmp/AnalysisResults.root": "LHC23zzh_apass2_544124"},
         only={"150642": "19415",
               "150796": "asd",
               "152893": "asd"}):
    results = []
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
        print(i[1], t)
        results.append(process_one_file(i[1], tag=t))
        # input("Press enter to continue...")
    legs = []
    for i in results[0]:
        range_x = [0, 10]
        if "VsRadius" in i:
            range_x = [0, 50]
        range_y = [0, 0.05]
        if i.endswith("mean"):
            range_y = [0.49, 0.52]

        can = draw_nice_canvas(i)
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
        leg.Draw()
        can.Modified()
        can.Update()

    input("Press enter to continue...")


main(argv[1:])
