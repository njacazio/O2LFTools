// This macro provides the comparison of the following variables in two different periods / passes :
// 0) mean of gaussian fits
// 1) sigma of gaussian fits
// 2) purity of selected sample
// 3) raw yields
// It takes in input the output of the post processing macro PostProcessV0AndCascQA_AO2D.C
// ========================================================================
//
// This macro was originally written by:
// chiara.de.martin@cern.ch

#include "TStyle.h"
#include "TFile.h"
#include "TFitResult.h"
#include "TH1F.h"
#include "TH2F.h"
#include "TH3F.h"
#include "TCanvas.h"
#include "TPad.h"
#include "TF1.h"
#include "TLatex.h"
#include "TLine.h"
#include "TRatioPlot.h"
#include "TLegend.h"
#include "TPad.h"
#include "TSpline.h"

void StyleHisto(TH1F *histo, Float_t Low, Float_t Up, Int_t color, Int_t style, TString titleX, TString titleY, TString title, Bool_t XRan\
ge,
                Float_t XLow, Float_t XUp, Float_t xOffset, Float_t yOffset, Float_t mSize)
{
  histo->GetYaxis()->SetRangeUser(Low, Up);
  if (XRange)
    histo->GetXaxis()->SetRangeUser(XLow, XUp);
  histo->SetLineColor(color);
  histo->SetMarkerColor(color);
  histo->SetMarkerStyle(style);
  histo->SetMarkerSize(mSize);
  histo->GetXaxis()->SetTitle(titleX);
  histo->GetXaxis()->SetLabelSize(0.05);
  histo->GetXaxis()->SetTitleSize(0.05);
  histo->GetXaxis()->SetTitleOffset(xOffset);
  histo->GetYaxis()->SetTitle(titleY);
  histo->GetYaxis()->SetTitleSize(0.05);
  histo->GetYaxis()->SetLabelSize(0.05);
  histo->GetYaxis()->SetTitleOffset(yOffset);
  histo->SetTitle(title);
}

void StyleCanvas(TCanvas *canvas, Float_t LMargin, Float_t RMargin, Float_t TMargin, Float_t BMargin)
{
  canvas->SetFillColor(0);
  canvas->SetTickx(1);
  canvas->SetTicky(1);
  canvas->SetLeftMargin(LMargin);
  canvas->SetRightMargin(RMargin);
  canvas->SetTopMargin(TMargin);
  canvas->SetBottomMargin(BMargin);
  gStyle->SetOptStat(0);
  gStyle->SetLegendBorderSize(0);
  gStyle->SetLegendFillColor(0);
  gStyle->SetLegendFont(42);
  // gStyle->SetPalette(55, 0);
}

void StylePad(TPad *pad, Float_t LMargin, Float_t RMargin, Float_t TMargin, Float_t BMargin)
{
  pad->SetFillColor(0);
  pad->SetTickx(1);
  pad->SetTicky(1);
  pad->SetLeftMargin(LMargin);
  pad->SetRightMargin(RMargin);
  pad->SetTopMargin(TMargin);
  pad->SetBottomMargin(BMargin);
}

TSpline3 *sp3;
Double_t spline(Double_t *x, Double_t *p)
{
  Double_t xx = x[0];
  return sp3->Eval(xx);
}

const Int_t numPart = 7;
const Int_t numChoice = 4; // mean, sigma, purity, yield
Float_t ParticleMassPDG[numPart] = {0.497611, 1.115683, 1.115683, 1.32171, 1.32171, 1.67245, 1.67245};

void CompareSigmaWidthPurity(TString year0 = "LHC22m_pass1",
                             TString year1 = "LHC16k_pass3",
                             TString Sfilein0 = "../Run3QA/LHC22m_pass1/PostProcessing_Train44413_22m.root",
                             TString Sfilein1 = "../LHC16k_pass3/PostProcessLHC16k_pass3.root",
                             TString OutputDir = "../Run3QA/LHC22m_pass1/",
                             Bool_t isPseudoEfficiency = 1,
                             TString SPublishedYieldForPseudoEff = "../PublishedYield13TeV/HEPData-ins1748157-v1-Table") // directory where published yields are stored
{

  Int_t Choice = 0;
  cout << "Do you want to compare Mean (=0), Sigma (=1), Purity (=2) or Yield per event (=3)?" << endl;
  cin >> Choice;
  if (Choice > (numChoice - 1))
  {
    cout << "Option not implemented" << endl;
    return;
  }
  if (isPseudoEfficiency == 1 && Choice != 3)
  {
    cout << "To compute pseudoefficiency you must compare Yields" << endl;
    return;
  }
  TString TypeHisto[4] = {"Mean", "Sigma", "Purity", "Yield"};
  TString Spart[numPart] = {"K0S", "Lam", "ALam", "XiMin", "XiPlu", "OmMin", "OmPlu"};
  TString NamePart[numPart] = {"K^{0}_{S}", "#Lambda", "#bar{#Lambda}", "#Xi^{-}", "#Xi^{+}", "#Omega^{-}", "#Omega^{+}"};
  TString TitleY[4] = {"Mean (GeV/#it{c}^{2})", "Sigma (GeV/#it{c}^{2})", "S/(S+B)", "1/#it{N}_{evt} d#it{N}/d#it{p}_{T} (GeV/#it{c})^{-1}"};
  TString TitleXPt = "#it{p}_{T} (GeV/#it{c})";

  Float_t YLowMean[numPart] = {0.485, 1.110, 1.110, 1.316, 1.316, 1.664, 1.664};
  Float_t YUpMean[numPart] = {0.51, 1.130, 1.130, 1.327, 1.327, 1.68, 1.68};
  Float_t YLowSigma[numPart] = {0.0002, 0.0002, 0.0002, 0.0002, 0.0002, 0.0002, 0.0002};
  Float_t YUpSigma[numPart] = {0.015, 0.015, 0.015, 0.015, 0.015, 0.015, 0.015};
  Float_t YLowPurity[numPart] = {0, 0, 0, 0, 0, 0, 0};

  Float_t YLow[numPart] = {0};
  Float_t YUp[numPart] = {0};
  Float_t YLowRatio[4] = {0.95, 0.9, 0.01, 0};
  Float_t YUpRatio[4] = {1.05, 3.0, 1, 0.05};

  TString Sfileout = OutputDir + "Compare" + TypeHisto[Choice];
  TFile *filein0 = new TFile(Sfilein0, "");
  if (!filein0)
  {
    cout << "No input file n.0" << endl;
    return;
  }
  TFile *filein1 = new TFile(Sfilein1, "");
  if (!filein1)
  {
    cout << "No input file n.1" << endl;
    return;
  }

  TH1F *histo0[numPart];
  TH1F *histo1[numPart];
  TH1F *histoRatio[numPart];
  TCanvas *canvas[numPart];
  TPad *pad1[numPart];
  TPad *pad2[numPart];

  for (Int_t part = 0; part < numPart; part++)
  {
    cout << "\n\e[35mParticle:\e[39m " << Spart[part] << endl;
    if (Choice == 0)
    {
      YLow[part] = YLowMean[part];
      YUp[part] = YUpMean[part];
    }
    else if (Choice == 1)
    {
      YLow[part] = YLowSigma[part];
      YUp[part] = YUpSigma[part];
    }
    else if (Choice == 2)
    {
      YLow[part] = YLowPurity[part];
      YUp[part] = 1;
    }

    TString inputName = TypeHisto[Choice] + "_" + Spart[part];
    histo0[part] = (TH1F *)filein0->Get(inputName);
    if (!histo0[part])
    {
      cout << "No histo name: " << inputName << " in file0" << endl;
      return;
    }
    histo0[part]->SetName(inputName + "_file0");
    histo1[part] = (TH1F *)filein1->Get(inputName);
    if (!histo1[part])
    {
      cout << "No histo name: " << inputName << " in file1" << endl;
      return;
    }
    histo1[part]->SetName(inputName + "_file1");

    // Ratios
    histoRatio[part] = (TH1F *)histo0[part]->Clone(inputName + "_Ratio");
    histoRatio[part]->Divide(histo1[part]);

    if (Choice == 3)
    {
      YLow[part] = 0;
      YUp[part] = 1.2 * histo1[part]->GetMaximum(histo1[part]->GetMaximumBin());
    }
    if (Choice != 3)
    {
      YLow[part] += 10e-5;
      if (Choice != 2)
        YUp[part] -= 10e-5;
    }

    canvas[part] = new TCanvas("canvas" + Spart[part], "canvas" + Spart[part], 1000, 800);
    StyleCanvas(canvas[part], 0.15, 0.05, 0.05, 0.15);
    pad1[part] = new TPad("pad1" + Spart[part], "pad1" + Spart[part], 0, 0.36, 1, 1);
    pad2[part] = new TPad("pad2" + Spart[part], "pad2" + Spart[part], 0, 0.01, 1, 0.35);
    StylePad(pad1[part], 0.15, 0.05, 0.05, 0.01);
    StylePad(pad2[part], 0.15, 0.05, 0.03, 0.2);

    TLegend *legend;
    if (Spart[part] == "XiPlu" && Choice == 0)
      legend = new TLegend(0.5, 0.25, 0.8, 0.45);
    else if (Spart[part] == "K0S" && Choice == 1)
      legend = new TLegend(0.5, 0.5, 0.8, 0.7);
    else if (part <= 2 && Choice == 2)
      legend = new TLegend(0.5, 0.25, 0.8, 0.45);
    else
      legend = new TLegend(0.5, 0.7, 0.8, 0.9);
    legend->AddEntry("", NamePart[part], "");

    StyleHisto(histo0[part], YLow[part], YUp[part], kRed + 2, 33, /*TitleXPt*/ "", TitleY[Choice], "", 0, 0, 0, 1.5, 1.5, 2);
    StyleHisto(histo1[part], YLow[part], YUp[part], kBlue + 2, 33, /*TitleXPt*/ "", TitleY[Choice], "", 0, 0, 0, 1.5, 1.5, 2);
    StyleHisto(histoRatio[part], YLowRatio[Choice], YUpRatio[Choice], kRed + 2, 33, TitleXPt, "Ratio to " + year1, "", 0, 0, 0, 1.5, 1.5, 2);
    histoRatio[part]->GetXaxis()->SetLabelSize(0.08);
    histoRatio[part]->GetXaxis()->SetTitleSize(0.08);
    histoRatio[part]->GetXaxis()->SetTitleOffset(1.2);
    histoRatio[part]->GetYaxis()->SetLabelSize(0.08);
    histoRatio[part]->GetYaxis()->SetTitleSize(0.08);
    histoRatio[part]->GetYaxis()->SetTitleOffset(0.8);

    TF1 *lineMass = new TF1("pol0", "pol0", 0, 8);
    lineMass->SetParameter(0, ParticleMassPDG[part]);
    lineMass->SetLineColor(kBlack);
    lineMass->SetLineStyle(7);

    canvas[part]->cd();
    pad1[part]->Draw();
    pad1[part]->cd();
    histo0[part]->Draw("same");
    histo1[part]->Draw("same");
    if (Choice == 0)
      lineMass->DrawClone("same");
    legend->AddEntry(histo0[part], year0, "pl");
    legend->AddEntry(histo1[part], year1, "pl");
    legend->Draw("");

    canvas[part]->cd();
    pad2[part]->Draw();
    pad2[part]->cd();
    histoRatio[part]->Draw("same");

    if (part == 0)
      canvas[part]->SaveAs(Sfileout + ".pdf(");
    else if (part == numPart - 1)
      canvas[part]->SaveAs(Sfileout + ".pdf)");
    else
      canvas[part]->SaveAs(Sfileout + ".pdf");
  }

  // Pseudoefficiency
  TH1F *histoPub[numPart];
  TH1F *histoNum[numPart];
  TH1F *histoRatioToPub[numPart];
  TDirectoryFile *dir;
  TString SfilePub = "";
  TString FileName[numPart] = {"1", "2", "2", "3", "3", "4", "4"};
  TString HistoNumber[numPart] = {"11", "11", "11", "11", "11", "6", "6"};
  TSpline3 *splinePub[numPart];
  TF1 *fsplinePub[numPart];
  TCanvas *canvasRatioToPub[numPart];
  TString SfileoutRatioToPub = OutputDir + "RatioToPub";
  Float_t YLowRatioToPub = 0;
  Float_t YUpRatioToPub = 0.01;
  Float_t LowPub[numPart] = {0, 0.4, 0.4, 0.6, 0.6, 0.9, 0.9}; // lowe values of published yields
  Float_t UpPub[numPart] = {10, 6.5, 6.5, 5.5, 5.5, 5.5, 5.5}; // upper value of published yields
  Float_t Low[numPart] = {0, 0.4, 0.4, 0.6, 0.6, 0.9, 0.9};
  Float_t Up[numPart] = {0, 6, 6, 4, 4, 4, 4};

  if (isPseudoEfficiency)
  {
    cout << "\n\n\e[35mComputation of pseudoefficiency \e[39m" << endl;
    for (Int_t part = 0; part < numPart; part++)
    {
      cout << "\n\e[35mParticle:\e[39m " << Spart[part] << endl;
      SfilePub = SPublishedYieldForPseudoEff + "_" + FileName[part] + ".root";
      TFile *filePub = new TFile(SfilePub, "");
      if (!filePub)
      {
        cout << "File " << SfilePub << " not available " << endl;
        return;
      }
      cout << "Input file with published yields: " << SfilePub << endl;
      dir = (TDirectoryFile *)filePub->Get("Table " + FileName[part]);
      if (!dir)
      {
        cout << "Input dir not available " << endl;
        return;
      }
      histoPub[part] = (TH1F *)dir->Get("Hist1D_y" + HistoNumber[part]);
      if (!histoPub[part])
      {
        cout << "Published histo not found" << endl;
        return;
      }
      histoPub[part]->SetName("histoYieldPub" + Spart[part]);
      if (part != 0)
        histoPub[part]->Scale(1. / 2); // particle and antiparticle yields are summed
      splinePub[part] = new TSpline3(histoPub[part], "Spline" + Spart[part]);
      sp3 = (TSpline3 *)splinePub[part]->Clone("SplineClone" + Spart[part]);
      fsplinePub[part] = new TF1("fSpline" + Spart[part], spline, 0, 10);

      histoNum[part] = (TH1F *)histo0[part]->Clone("histoNum" + Spart[part]);
      for (Int_t b = 1; b <= histoPub[part]->GetNbinsX(); b++)
      {
        // cout << fsplinePub[part]->Eval(histoPub[part]->GetBinCenter(b)) << " vs "
        //<< histoPub[part]->GetBinContent(b) << endl;
      }
      histoRatioToPub[part] = (TH1F *)histoNum[part]->Clone("RatioToPub" + Spart[part]);
      for (Int_t b = 1; b <= histoNum[part]->GetNbinsX(); b++)
      {
        Float_t ALow = histoNum[part]->GetXaxis()->GetBinLowEdge(b);
        Float_t AUp = histoNum[part]->GetXaxis()->GetBinUpEdge(b);
        if (fsplinePub[part]->Integral(ALow, AUp) <= 0)
          continue;
        Float_t Numerator = histoNum[part]->GetBinContent(b) * histoNum[part]->GetBinWidth(b);
        histoRatioToPub[part]->SetBinContent(b, Numerator / fsplinePub[part]->Integral(ALow, AUp));
        // cout << histoNum[part]->GetBinCenter(b) << " Alow: " << ALow << " AUp " << AUp << endl;
        // cout << histoNum[part]->GetBinContent(b) << " +- " << histoNum[part]->GetBinError(b) << endl;
        // cout << fsplinePub[part]->Integral(ALow, AUp) << " +- " << fsplinePub[part]->IntegralError(ALow, AUp) << endl;
        // cout << histoRatioToPub[part]->GetBinContent(b) << " +- " << histoRatioToPub[part]->GetBinError(b) << endl;
        histoRatioToPub[part]->SetBinError(b, sqrt(
                                                  pow(histoNum[part]->GetBinError(b) / histoNum[part]->GetBinContent(b), 2) +
                                                  pow(fsplinePub[part]->IntegralError(ALow, AUp) / fsplinePub[part]->Integral(ALow, AUp), 2)) *
                                                  histoRatioToPub[part]->GetBinContent(b));
      }
      canvasRatioToPub[part] = new TCanvas("canvasRatioToPub" + Spart[part], "canvasRatioToPub" + Spart[part], 1000, 800);
      StyleCanvas(canvasRatioToPub[part], 0.15, 0.05, 0.05, 0.15);

      TLegend *legendRatioToPub = new TLegend(0.4, 0.6, 0.8, 0.8);
      legendRatioToPub->AddEntry("", NamePart[part], "");
      legendRatioToPub->AddEntry("", year0, "");

      if (part > 2)
        YUpRatioToPub = 0.001;
      // YUpRatioToPub = 0.5; //this is OK for Run 2
      StyleHisto(histoRatioToPub[part], YLowRatioToPub, YUpRatioToPub, kRed + 2, 33, TitleXPt, "Ratio to published yield", "", 0, 0, 0, 1.5, 1.5, 2);
      histoRatioToPub[part]->GetXaxis()->SetRangeUser(Low[part], Up[part]);
      histoRatioToPub[part]->Draw("");
      legendRatioToPub->Draw("");
      if (part == 0)
        canvasRatioToPub[part]->SaveAs(SfileoutRatioToPub + ".pdf(");
      else if (part == numPart - 1)
        canvasRatioToPub[part]->SaveAs(SfileoutRatioToPub + ".pdf)");
      else
        canvasRatioToPub[part]->SaveAs(SfileoutRatioToPub + ".pdf");
    }
  }

  cout << "\nI started from the files: " << endl;
  cout << Sfilein0 << "\n"
       << Sfilein1 << endl;

  cout << "\nI created the file: " << endl;
  cout << Sfileout << endl;
}
