import argparse
import copy
import csv
import itertools as it
import re
import socket
import sys


# keep 3 decimal places
def fmt_arr(arr):
    return map(lambda x: round(float(x), 3), arr)


def parse(solver, data, hname):
    files = {
        "s": f"RunTimeSummarise-D-S-{solver}.out",
        "p": f"RunTimeSummarise-D-P-{solver}.out",
        "l": f"RunTimeSummarise-L-P-{solver}.out",
    }
    for k, filename in files.items():
        with open(filename, "r") as f:
            arr = re.findall(r"\b\d+(?:\.\d+)?\b", f.read())

            targets = arr[1::3]
            arr_elapse = fmt_arr(arr[2::3])
            # consume? unknown
            arr_cost = fmt_arr(it.accumulate(copy.deepcopy(arr_elapse)))

            if k != "s":  # possibility
                targets = [f"2^{{-{i}}}" for i in targets]

            data["round"] = list(range(1, len(targets) + 1))
            sname = solver[:3].lower()
            data.setdefault(f"M_{k}", targets)
            data.setdefault(f"E_{{{sname}}}^{{{hname},{k}}}", list(arr_elapse))
            data.setdefault(f"T_{{{sname}}}^{{{hname},{k}}}", list(arr_cost))


def write_csv(data, filename, fieldnames, args):
    with open(filename, "w") as f:
        # fieldnames = ["round"]

        def do_write(f):
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            for i in range(len(data[fieldnames[0]])):
                row = {key: data[key][i] for key in fieldnames}
                w.writerow(row)

        do_write(f)
        if args.o:
            do_write(sys.stdout)
    w = csv.DictWriter(f, fieldnames=fieldnames)


if __name__ == "__main__":
    # s = sys.argv[1]
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-o", default=False, action="store_true", help="also pipe to stdout"
    )
    args = parser.parse_args()

    # to be written to csv
    solvers = {
        "cadical": {},
        "cryptominisat": {},
        "kissat": {},
        "glucose-syrup": {},
        "maplesat": {},
    }

    # if s not in solvers.keys():
    #     print(f"no such sovler: {s}")
    #     sys.exit(1)

    alias = {"arch": "B", "cb": "A"}
    hname = socket.gethostname()
    if hname in alias.keys():
        hname = alias[hname]

    for solver, data in solvers.items():
        sname = solver[:3].lower()
        parse(solver, data, hname)
        write_csv(
            data,
            f"A-{solver}.csv",
            # terrible ex...
            # '<,'>s/\(p\|s\|l\)-\(target\)/$M_\1$/g
            # '<,'>s/\(s\|p\|l\)-\(elapse\|cost\)/\=get({'E': 'E', 'C':'T'}, toupper(strpart(submatch(2),0,1))) . "_{{}}^"
            [
                "round",
                "M_s",
                f"E_{{{sname}}}^{{{hname},s}}",
                f"T_{{{sname}}}^{{{hname},s}}",
                "M_p",
                f"E_{{{sname}}}^{{{hname},p}}",
                f"T_{{{sname}}}^{{{hname},p}}",
                "M_l",
                f"E_{{{sname}}}^{{{hname},l}}",
                f"T_{{{sname}}}^{{{hname},l}}",
            ],
            args,
        )

    # or, to json, then to table https://www.convertcsv.com/json-to-csv.htm
    # print(json.dumps(solvers["cadical"], indent=4))
