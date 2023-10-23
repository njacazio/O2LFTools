#!/usr/bin/env python3


"""
Script to produce the plots of the PID purity and separation power
"""

from ROOT import TFile, TH1, TCanvas, TLegend, gPad, TColor, TGraphErrors, TLatex, TLine
from numpy import sqrt
from argparse import ArgumentParser


def get(fname, particle, hypo, tag, det="TOF", print_eta=False, use_momentum=False):
    colors = {"El": '#e41a1c', "Mu": '#377eb8',
              "Pi": '#4daf4a', "Ka": '#984ea3', "Pr": '#ff7f00'}
    f = TFile(fname, "READ")
    if not f.IsOpen():
        print("No file", fname, "found")
        return
    d = f"pid{det}-qa-{hypo}"
    d = "pid-t-o-f-task-q-a-m-c"
    f.Get(d).ls()
    if not f.Get(d):
        f.ls()
        raise ValueError("Did not find directory " + d)
    eta = f.Get(f"{d}/eta")
    if print_eta and eta:
        print("Eta range:",
              eta.GetXaxis().GetBinLowEdge(eta.FindFirstBinAbove(0, 1, eta.FindBin(0))),
              eta.GetXaxis().GetBinLowEdge(eta.FindLastBinAbove(0, 1, eta.FindBin(0))))
    d2 = f"{d}/nsigmaMCprm"
    f.Get(d2).ls()
    if use_momentum:
        d2 += "vsp"
    if not f.Get(d2):
        print("Did not find directory", d2)
        f.Get(d).ls()
        return
    d = d2
    h = f"{d}/{particle}/{particle}"
    h = f.Get(h)
    if not h:
        print("Did not find histogram", h)
        f.Get(d2).ls()
        return
    h.SetDirectory(0)
    f.Close()
    col = TColor.GetColor(colors[particle])
    if 0:
        print(h.GetNbinsX(),
              h.GetXaxis().GetBinLowEdge(1),
              h.GetXaxis().GetBinUpEdge(h.GetNbinsX()))
    h.SetLineWidth(2)
    h.SetLineColor(col)
    h.SetMarkerColor(col)
    tit = h.GetTitle()
    h.SetTitle(tit + tag)
    h.SetBit(TH1.kNoStats)
    return h


def get_all(fname, particle="El", tag="", det="TOF", use_momentum=False):
    h = {}
    for i in "El Mu Pi Ka Pr".split():
        h[i] = get(fname, i, particle, tag, det=det, use_momentum=use_momentum)
        print(h[i])
    return h, particle, tag, det

CANVAS_LIST = []
def canvas(n="", dim=[1000, 800], m_l=0.15, m_r=0.15, tag="", dont_draw=False, logx=True, logy=False):
    c = TCanvas(n + tag, n + tag, int(dim[0]), int(dim[1]))
    c.SetLogx(logx)
    c.SetLogy(logy)
    c.SetLogz()
    c.SetTicky()
    c.SetTickx()
    c.SetLeftMargin(m_l)
    c.SetRightMargin(m_r)
    if not dont_draw:
        c.Draw()
    CANVAS_LIST.append(c)
    return c


def make_frame(l, h, x, y):
    f = gPad.DrawFrame(*l, *h, ";" + x + ";"+y)
    f.GetXaxis().SetTitleOffset(1.2)
    return f


def plot(h, x=[0, 5], y=[-5, 5], logx=True, cut=3,
         draw_contamination=True, save=False,
         dont_draw=False, percent=False):
    h, particle, tag, det = h

    can = canvas("nsigma"+particle, tag=tag, dont_draw=dont_draw)
    frame = make_frame([x[0], y[0]], [x[1], y[1]],
                       h[particle].GetXaxis().GetTitle(),
                       h[particle].GetYaxis().GetTitle())
    frame.SetDirectory(0)
    frame.SetLineWidth(0)
    leg = TLegend(.75, .8, .84, .89)
    leg.SetLineColor(0)
    leg.SetNColumns(2)
    in_cut = {}
    t = {"El": "e", "Mu": "#mu", "Pi": "#pi", "Ka": "K", "Pr": "p"}

    def clean_histo(h):
        for j in range(1, h.GetNbinsX()+1):  # Clean histos
            xl = h.GetXaxis().GetBinLowEdge(j)
            xu = h.GetXaxis().GetBinUpEdge(j)
            if xl > x[0] and xu < x[1]:
                continue
            h.SetBinContent(j, 0)
            h.SetBinError(j, 0)

    profiles = {}
    for i in h:
        h[i].Draw("same")
        profiles[i] = h[i].ProfileX("profile"+i)
        profiles[i].SetDirectory(0)
        leg.AddEntry(h[i], t[i])
        in_cut[i] = h[i].ProjectionX(f"{i}_in_{cut}_sigma_{tag}_{det}_{particle}",
                                     h[i].GetYaxis().FindBin(-cut),
                                     h[i].GetYaxis().FindBin(cut))
        in_cut[i].Sumw2()
        clean_histo(profiles[i])
    leg.Draw()
    can_prof = canvas("profile"+particle, tag=tag)
    can_prof.cd()
    frame.Draw()
    for i in profiles:
        profiles[i].Draw("same")

    total = in_cut["El"].Clone("Total")
    total.Reset()
    for i in in_cut:
        total.Add(in_cut[i])
    leg.Draw()
    can.Update()
    can2 = canvas("Purity"+particle, tag=tag)
    if percent:
        frame2 = make_frame([x[0], 0], [x[1], 101], h[particle].GetXaxis().GetTitle(), f"{t[particle]} purity in #pm{int(cut)}N#sigma (%)")
    else:
        frame2 = make_frame([x[0], 0], [x[1], 1.1], h[particle].GetXaxis().GetTitle(), f"{t[particle]} purity in #pm{int(cut)}N#sigma (%)")
    for i in in_cut:
        in_cut[i].Divide(in_cut[i], total, 1., 1., "B")
#         in_cut[i].Divide(total)
        if percent:
            in_cut[i].Scale(100)
#             in_cut[i].Divide(in_cut[i], total, 100, 1, "B")
#         else:
#             in_cut[i].Divide(in_cut[i], total, 1, 1, "B")
        clean_histo(in_cut[i])

    graphs = {}
    if draw_contamination:
        for i in in_cut:
            if 1:
                graphs[i] = TGraphErrors()
                graphs[i].SetName("g_"+in_cut[i].GetName())
                graphs[i].SetTitle("g_"+in_cut[i].GetTitle())
                graphs[i].SetLineColor(in_cut[i].GetLineColor())
                graphs[i].SetMarkerColor(in_cut[i].GetLineColor())
                graphs[i].SetMarkerStyle(8)
                for j in range(1, in_cut[i].GetNbinsX()+1):
                    x = in_cut[i].GetXaxis().GetBinCenter(j)
                    y = in_cut[i].GetBinContent(j)
                    if y > 0:
                        graphs[i].SetPoint(graphs[i].GetN(), x, y)
                graphs[i].Draw("PLsame")
            else:
                in_cut[i].Draw("same")
        leg.Draw()
    else:
        in_cut[particle].Draw("same")
    can2.Update()
    if save:
        can.SaveAs(f"{det}_{particle}_nsigma.pdf")
        can_prof.SaveAs(f"{det}_{particle}_separation.pdf")
        can2.SaveAs(f"{det}_{particle}_purity.pdf")
    return {"canvases": [can, can_prof, can2], "histo": h, "frame": frame, "frame_purity": frame2, "leg": leg, "g": graphs, "purity": in_cut, "p": profiles}


def draw_purity(data, contamination, labels=None, y=None, tags=None, canvas_tag="", color_offset=0):
    if type(data) is not list:
        data = [data]
    colors = ["#0066ff", "#000000", '#e41a1c', '#377eb8', '#4daf4a']
    p = {"El": "e", "Pi": "#pi", "Ka": "K", "Pr": "p"}
    p_long = {"El": "electron", "Pi": "pion", "Ka": "kaon", "Pr": "proton"}
    markers = [20, 21]
    marker_sizes = [1.5, 1.5]
    can = canvas("purity"+contamination+canvas_tag)
    frame = data[0]["frame_purity"].DrawCopy()
    tit = f"{p_long[contamination]} purity"
    frame.GetYaxis().SetTitle(tit)
    if y is not None:
        frame.GetYaxis().SetRangeUser(*y)
    xframe = [frame.GetXaxis().GetBinLowEdge(1),
              frame.GetXaxis().GetBinUpEdge(frame.GetNbinsX())]
    separations = {}
    leg = None
    if tags is not None:
        leg = TLegend(0.26, .4, 0.46, .52)
        leg.SetLineColor(0)
        leg.Draw("same")

    for j, h in enumerate(data):
        col = TColor.GetColor(colors[j+color_offset])
#         print(h)
        for i in h["purity"]:
            if i not in contamination:
                continue
            p = h["purity"][i]
            t = f"{i}_{j}"
            if tags is not None:
                t = tags[j]
            s = TGraphErrors()
            if tags is not None:
                s.SetTitle(tags[j])
            s.SetLineColor(p.GetLineColor())
            s.SetMarkerColor(p.GetMarkerColor())
            s.SetLineColor(col)
            s.SetMarkerColor(col)
            s.SetMarkerStyle(markers[j+color_offset])
            s.SetMarkerSize(marker_sizes[j+color_offset])
            s.SetLineWidth(2)
            separations[t] = s
            y = []
            ye = []
            x_bin = []
            for j in range(1, p.GetNbinsX()+1):
                #                 if p.GetXaxis().GetBinUpEdge(j)+0.1 > x[1]:
                #                     continue
                y.append(abs(p.GetBinContent(j)))
                if y[-1] <= 0:
                    continue
                ye.append(p.GetBinError(j))
                x_bin.append(p.GetXaxis().GetBinCenter(j))
                square_sum = 0
                for k in ye:
                    square_sum += k*k
                square_sum = sqrt(square_sum)
                if square_sum/(sum(y)/len(y)) < 0.5 or 1:
                    s.SetPoint(s.GetN(), sum(x_bin)/len(x_bin), sum(y)/len(y))
                    s.SetPointError(s.GetN()-1, 0, square_sum)
                    y = []
                    ye = []
                    x_bin = []
            s.Draw("PLsame")
            if leg is not None:
                leg.AddEntry(s, "", "pl")
    l = []
    if labels is not None:
        for i in labels:
            label = TLatex(labels[i][0], labels[i][1], i)
            label.SetTextSize(labels[i][2])
            label.SetTextAlign(labels[i][3])
            label.SetTextFont(42)
            label.SetNDC()
            label.Draw()
            l.append(label)
    can.Update()
    return can, separations, l, frame, leg


def draw_separation_power(data, contamination="Pi", labels=None,
                          level=3, y=[0, 10], tags=None, canvas_tag="", color_offset=0):
    if type(data) is not list:
        data = [data]
    colors = ["#0066ff", "#000000", '#e41a1c', '#377eb8', '#4daf4a']
    p = {"Pi": "#pi", "Ka": "K", "Pr": "p"}
    markers = [20, 21]
    marker_sizes = [1.5, 1.5]
    can = canvas("separation"+contamination+canvas_tag)
    frame = data[0]["frame"].DrawCopy()
    tit = frame.GetYaxis().GetTitle()
    tit = tit.replace("N", "n").replace("(", "").replace(")", "").replace("^{RICH}", "").replace("_{#sigma}", "#sigma_{")+p[contamination]+"}"
    frame.GetYaxis().SetTitle(tit)
    frame.GetYaxis().SetRangeUser(*y)
    x = [frame.GetXaxis().GetBinLowEdge(1), frame.GetXaxis().GetBinUpEdge(frame.GetNbinsX())]
    separations = {}
    leg = None
    if tags is not None:
        leg = TLegend(0.26, .4, 0.46, .52)
        leg.SetLineColor(0)
        leg.Draw("same")

    for j, h in enumerate(data):
        col = TColor.GetColor(colors[j+color_offset])
        for i in h["p"]:
            if i not in contamination:
                continue
            p = h["p"][i]
            t = f"{i}_{j}"
            if tags is not None:
                t = tags[j]
            s = TGraphErrors()
#             s = TH1F(t+"_separation", t+"_separation", p.GetNbinsX(), p.GetXaxis().GetXbins().GetArray())
            if tags is not None:
                s.SetTitle(tags[j])
            s.SetLineColor(col)
            s.SetMarkerColor(col)
            s.SetMarkerStyle(markers[j+color_offset])
            s.SetMarkerSize(marker_sizes[j+color_offset])
            s.SetLineWidth(2)
            separations[t] = s
            for j in range(1, p.GetNbinsX()+1):
                y = abs(p.GetBinContent(j))
                if y <= 0:
                    continue
                ye = p.GetBinError(j)
                if p.GetXaxis().GetBinUpEdge(j)+0.1 > x[1]:
                    continue
#                 s.SetBinContent(j, y)
#                 s.SetBinError(j, ye)
                s.SetPoint(s.GetN(), p.GetXaxis().GetBinCenter(j), y)
                s.SetPointError(s.GetN()-1, 0, ye)
            s.Draw("PLsame")
            if leg is not None:
                leg.AddEntry(s, "", "pl")
    l = []
    if labels is not None:
        for i in labels:
            label = TLatex(labels[i][0], labels[i][1], i)
            label.SetTextSize(labels[i][2])
            label.SetTextAlign(labels[i][3])
            label.SetTextFont(42)
            label.SetNDC()
            label.Draw()
            l.append(label)
    if level is not None:
        x = frame.GetXaxis().GetBinLowEdge(1)
        label = TLatex(x*1.1, level*1.1, f"{int(level)}#sigma")
        label.SetTextSize(0.03)
        label.SetTextAlign(13)
        label.SetTextFont(42)
        label.Draw()
        l.append(label)
        level = TLine(x, level, frame.GetXaxis().GetBinUpEdge(frame.GetNbinsX()), level)
        level.SetLineStyle(2)
        level.Draw()
    can.Update()
    return can, separations, l, level, frame, leg


def draw_all_separations_purity(files=["/tmp/QAResults_RICHTOFSmallEta.root",
                                       "/tmp/QAResults_RICHTOFLargeEta.root"],
                                det="bRICH", particles=["El", "Pi", "Ka", "Pr"],
                                tags={"/tmp/QAResults_RICHTOFSmallEta.root": "SmallEta",
                                      "/tmp/QAResults_RICHTOFLargeEta.root": "LargeEta"},
                                labels={"Pb-Pb, #sqrt{#it{s}_{NN}} = 5.42 TeV": [.24, .75, 0.032, 15],
                                        "Pythia8 / Argantyr": [.24, .73, 0.032, 13],
                                        "ALICE 3 study": [0.35, .68, 0.038, 23],
                                        "Layout v1": [0.35, .63, 0.033, 23],
                                        "barrel RICH": [0.35, .58, 0.028, 23]},
                                eta_tags=["|#it{#eta}| < 0.25", "0.75 < |#it{#eta}| < 1.25"],
                                use_momentum=False):
    histos = {}
    for i in files:
        histos[i] = {}
        for p in particles:
            histos[i][p] = get_all(i, particle=p, det=det, tag=tags.setdefault(i, i), use_momentum=use_momentum)

    def do_plot(hyp, cont, xrange, yrange=[-30, 30]):
        p = [plot(histos[i][hyp], x=xrange, y=yrange, draw_contamination=False) for i in histos]
        sep = draw_separation_power(p, cont, labels, tags=eta_tags)
        return p, sep

    electron, sep_electron = None, None
    if "El" in particles and "Pi" in particles:
        electron, sep_electron = do_plot("El", "Pi", [0.1, 50] if use_momentum else [0.1, 10])

    pion, sep_pion = do_plot("Pi", "Ka", [0.1, 300] if use_momentum else [0.1, 20])

    kaon, sep_kaon = do_plot("Ka", "Pr", [0.1, 300] if use_momentum else [0.1, 40])

    proton = [plot(histos[i]["Pr"], x=[0.1, 300] if use_momentum else [0.1, 40],
                   y=[-30, 30], draw_contamination=False) for i in histos]

    purity_labels = {"3#sigma PID (#varepsilon = 99%)": [0.35, .54, 0.028, 23]}
    for i in labels:
        purity_labels[i] = labels[i]

    electron_purity = None
    if electron:
        electron_purity = draw_purity(electron, contamination="El", labels=purity_labels, tags=eta_tags)

    pion_purity = draw_purity(pion, contamination="Pi", labels=purity_labels,
                              tags=eta_tags)

    kaon_purity = draw_purity(kaon, contamination="Ka", labels=purity_labels,
                              tags=eta_tags)

    proton_purity = draw_purity(proton, contamination="Pr", labels=purity_labels,
                                tags=eta_tags)

    return {"plot": [electron, pion, kaon, proton],
            "separation": [sep_electron, sep_pion, sep_kaon],
            "purity": [electron_purity, kaon_purity, proton_purity],
            "purity_dic": {"El": electron_purity, "Pi": pion_purity, "Ka": kaon_purity, "Pr": proton_purity}}


def draw_together(data, label_pad=1, canvas_tag="",
                  logx=True, save_as=None,
                  deltax_nsigma=.15, deltay_nsigma=.4,
                  deltax=1, deltay=0):
    can = canvas("SeparationPower"+canvas_tag, [1600, 600])
    gPad.SetMargin(0, 0, 0, 0)
    can.Divide(len(data), 1, 0, 0)
    for i in enumerate(data):
        pad_index = 1+i[0]
        can.cd(pad_index).SetMargin(0, 0, 0, 0)
        i[1][0].DrawClonePad()
        gPad.SetMargin(0.12, 0.03, 0.15, 0.1)
        gPad.SetLogx(logx)
        clean_pad = False
        if label_pad is not None and i[0] != label_pad:
            clean_pad = True
        l = gPad.GetListOfPrimitives()
        if l:
            for j in range(l.GetEntries()-1, -1, -1):
                obj = l.At(j)
                cn = obj.ClassName()
                if "TLatex" in cn:
                    if "3#sigma" == l.At(j).GetTitle():
                        obj.SetNDC()
                        obj.SetX(deltax_nsigma)
                        obj.SetY(deltay_nsigma)
                        continue
                    else:
                        obj.SetX(obj.GetX()+deltax)
                        obj.SetY(obj.GetY()+deltay)
                    if clean_pad:
                        l.RemoveAt(j)
                elif "TLegend" in cn:
                    obj.SetX1NDC(obj.GetX1NDC()+deltax)
                    obj.SetX2NDC(obj.GetX2NDC()+deltax)
                    if clean_pad:
                        l.RemoveAt(j)
                elif "TH1" in cn:
                    #                     print(pad_index, ")", obj.GetName(), cn, i[0])
                    if "frame" in obj.GetName():
                        xaxis = obj.GetXaxis()
                        xaxis.SetLabelSize(0.045)
                        xaxis.SetLabelOffset(0.0)
                        xaxis.SetTitleSize(0.05)
                        yaxis = obj.GetYaxis()
                        yaxis.SetLabelSize(0.045)
                        yaxis.SetTitleSize(0.045)
        gPad.Update()
    if save_as is not None:
        can.SaveAs(save_as)
    return can


if __name__ == "__main__":
    inner_tof = draw_all_separations_purity(files=["/tmp/AnalysisResults.root"],
                                            det="TOF",
                                            particles=["El", "Pi", "Ka", "Pr"],
                                            tags={"/tmp/AnalysisResults.root": "Inner"},
                                            labels={"Pb-Pb, #sqrt{#it{s}_{NN}} = 5.42 TeV": [.24, .75, 0.032, 15],
                                                    "Pythia8 / Argantyr": [.24, .73, 0.032, 13],
                                                    "ALICE 3 study": [0.35, .68, 0.038, 23],
                                                    "Layout v1": [0.35, .63, 0.033, 23],
                                                    "barrel TOF": [0.35, .58, 0.028, 23]},
                                            eta_tags=["|#it{#eta}| < 0.25", "0.75 < |#it{#eta}| < 1.25"],
                                            use_momentum=False)
    for i in CANVAS_LIST:
        i.Modified()
        i.Update()
    input("Press enter to continue")
