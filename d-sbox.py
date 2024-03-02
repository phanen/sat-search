import argparse

from common import *

SearchRoundStart = 1
SearchRoundEnd = 10
InitialLowerBound = 0

cnfbuilders = [
    cnfbuilder_diff_sbox,
    cnfbuilder_diff_prob,
]

boxes = [
    SymbolicCNFConstraintForSbox43,  # diff-sbox
    SymbolicCNFConstraintForSbox55,  # diff-prob
    SymbolicCNFConstraintForSbox39,  # linear-sbox
    SymbolicCNFConstraintForSbox51,  # linear-bias
]


def run(args):
    satsolver = solver_builder(args.solver)
    cnfbuilder = cnfbuilders[(args.linear << 1) + args.prob]
    box = boxes[(args.linear << 1) + args.prob]

    tf = open(TIME, "a")
    roundOrProb = InitialLowerBound
    tick("total")
    for round in range(SearchRoundStart, SearchRoundEnd):
        tick("round")
        matsuiRoundIndex, matsuiCount = matsui(round)
        while True:
            cnfbuilder(
                round,
                roundOrProb,
                matsuiRoundIndex,
                matsuiCount,
                box,
                f"R{round}-A{roundOrProb}.cnf",
            )
            if args.sbva:
                reduce_by_sbva(f"R{round}-A{roundOrProb}.cnf")

            tick("sat")
            flag = satsolver(
                f"R{round}-A{roundOrProb}.cnf", f"R{round}-A{roundOrProb}.out"
            )
            tick("sat")
            log(
                f"\tRound: {round}; Active: {roundOrProb:2}; {flag:1}; Cost: {cost('sat')}"
            )
            roundOrProb += 1
            if flag:
                break
        Result[round] = roundOrProb - 1
        tick("round")
        tf.write(f"Round: {round}; Active: {roundOrProb - 1}; Cost: {cost('round')}\n")
    tick("total")
    tf.write(f"Total Runtime: {cost('total')}\n\n")
    tf.close()
    log(Result)
    log(f"Total Runtime: {cost('total')}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--solver", type=str, required=True)
    parser.add_argument("--sbva", action="store_true")
    parser.add_argument("-p", "--prob", default=False, action="store_true")
    parser.add_argument("-l", "--linear", default=False, action="store_true")
    args = parser.parse_args()
    run(args)
