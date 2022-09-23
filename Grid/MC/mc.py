#!/usr/bin/env python3

"""
Setup of the MC for LF
"""


from jinja2 import Template, Environment, FileSystemLoader, StrictUndefined
from os import path
import argparse
import getpass
from datetime import date, timedelta

jinjaEnv = Environment(loader=FileSystemLoader(searchpath="./templates/"),
                       undefined=StrictUndefined)


available_templates = []


def render_template_file(file_name,
                         template_data,
                         enable=True,
                         verbose=True):
    lines = []
    # if file_name.endswith(".tex"):
    #     if file_name not in available_templates:
    #         raise ValueError(file_name, "not in", available_templates)
    #     available_templates.remove(file_name)
    #     for i in template_data:
    #         template_data[i] = template_data[i].replace(
    #             "_", "\\_").replace("\\\_", "\\_")
    for i in template_data:
        t = template_data[i]
        if type(t) is list:
            t = "\", ".join(t)
            template_data[i] = f"{t}"

    if verbose:
        with open(path.join("./templates/", file_name), "r") as f:
            for i in f:
                i = i.strip()
                if len(i) == 0:
                    continue
                if i.startswith("%"):
                    continue
                j2_template = Template(i, undefined=StrictUndefined)
                l = j2_template.render(template_data)
                if verbose:
                    print("  ", i)
                    print("->", l)
                lines.append(l)
    else:
        lines = jinjaEnv.get_template(file_name).render(template_data)
    # out_file = ".".join(path.basename(file_name).split(".")[:-1])
    # out_file = path.join("rendered",
    #                      out_file + "."+path.basename(file_name).split(".")[-1])
    # with open(out_file, "w") as f:
    #     if not enable:
    #         f.write(f"% Disabled file from {file_name}\n")
    #     for i in lines.split("\n"):
    #         i = i.strip()
    #         f.write(f"{i}\n")


def main():
    yesterday = str((date.today() - timedelta(days=1))).replace("-", "")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--user", "-u", type=str, default=getpass.getuser())
    parser.add_argument("--name", "-n", type=str, default="mc.jdl")
    parser.add_argument("--relpath", "-p", type=str, default="MC")
    parser.add_argument("--o2dpg", type=str,
                        default=f"VO_ALICE@O2DPG::nightly-{yesterday}-1")
    parser.add_argument("--o2", type=str, default=None)
    parser.add_argument("--split", type=str, default="2")
    parser.add_argument("--o2physics", type=str,
                        default=f"VO_ALICE@O2Physics::nightly-{yesterday}-1")
    args = parser.parse_args()

    template_data = {}
    template_data["User"] = args.user
    template_data["JobTag"] = "VO_ALICE@O2sim::v20220718-1"
    template_data["Packages"] = [args.o2dpg]
    if args.o2 is not None:
        template_data["Packages"].append(args.o2)
    template_data["Packages"].append(args.o2physics)
    template_data["Executable"] = "/alice/cern.ch/user/a/aliprod/LHC21i1/o2_o2dpg_sim_v3.sh"
    template_data["InputFile"] = ["LF:/alice/cern.ch/user/a/aliprod/LHC21i3/runBeautyToJpsi_midy_pp_update_13.6TeV.sh",
                                  "LF:/alice/cern.ch/user/a/aliprod/LHC21i3/bcPattern_25ns_2556b_2544_2215_2332_144bpi_20injV3.root"]
    template_data["Type"] = "VO_ALICE@O2sim::v20220718-1"
    template_data["JDLPath"] = f"/alice/cern.ch/user/{args.user[0]}/{args.user}/{args.relpath}/{args.name}.jdl"
    template_data["Split"] = args.split

    render_template_file("mc.jdl", template_data)


main()
