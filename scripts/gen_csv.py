import copy
import csv
import itertools as it
import re
import sys

# import sys
# solver = sys.argv[1]


# keep 3 decimal places
def fmt_arr(arr):
    return map(lambda x: round(float(x), 3), arr)


def parse(solver, data):
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

            data.setdefault(k + "-target", targets)
            data.setdefault(k + "-elapse", list(arr_elapse))
            data.setdefault(k + "-cost", list(arr_cost))


# def write_latex_tab(tbl):
#     tbl


if __name__ == "__main__":
    # to be written to csv
    solvers = {
        "cadical": {},
        # "cryptominisat": {},
        # "kissat": {},
        # "glucose-syrup": {},
        # "maplesat": {},
    }

    for solver, data in solvers.items():
        parse(solver, data)

        data["round"] = list(range(1, 1 + len(data["s-target"])))
        with open(f"result-{solver}.csv", "w") as f:
            # fieldnames = ["round"]
            fieldnames = [
                "round",
                "s-target",
                "s-elapse",
                "s-cost",
                "p-target",
                "p-elapse",
                "p-cost",
                "l-target",
                "l-elapse",
                "l-cost",
            ]

            def do_write(f):
                w = csv.DictWriter(f, fieldnames=fieldnames)
                w.writeheader()
                for i in range(len(data[fieldnames[0]])):
                    row = {key: data[key][i] for key in fieldnames}
                    w.writerow(row)

            do_write(f)
            do_write(sys.stdout)
            # w = csv.DictWriter(f, fieldnames=fieldnames)

            # print(f"Error occurred: {str(e)}")
    # or, to json, then to table https://www.convertcsv.com/json-to-csv.htm
    # print(json.dumps(solvers["cadical"], indent=4))
