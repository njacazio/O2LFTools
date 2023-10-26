#!/usr/bin/env python3


"""
Script to trend variables run per run
"""

from download_hyperloop_per_run import get_run_per_run_files
from ROOT import TH1F, TCanvas


def main(hyperloop_train):
    l = get_run_per_run_files()
    can = TCanvas("asd")
    can.Draw()
    trend = TH1F("trend", "trend", len(l), 0, len(l))
    for i in l:
        # i.draw("v0cascades-q-a/histos-V0/DecayLengthLambda")
        # input("ASD")
        h = i.get("v0cascades-q-a/histos-V0/DecayLengthLambda")
        i.fill_histo(trend, "v0cascades-q-a/histos-V0/DecayLengthLambda", "mean")
    trend.Draw()
    can.Modified()
    can.Update()
    input("Press enter to continue")


main("asd")
