import argparse

from common import *

SymbolicCNFConstraintForSbox = SymbolicCNFConstraintForSbox43


def run(args):
    satsolver = solver_builder(args.solver)
    cnfbuilder = cnfbuilder_diff_prob if args.prob else cnfbuilder_diff_sbox
    tf = open(TIME_OUT, "a")
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
                SymbolicCNFConstraintForSbox,
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
        DiffActiveSbox[round] = roundOrProb - 1
        tick("round")
        tf.write(f"Round: {round}; Active: {roundOrProb - 1}; Cost: {cost('round')}\n")
    tick("total")
    tf.write(f"Total Runtime: {cost('total')}\n\n")
    tf.close()
    log(DiffActiveSbox)
    log(f"Total Runtime: {cost('total')}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--solver", type=str, required=True)
    parser.add_argument("--sbva", action="store_true")
    parser.add_argument("-p", "--prob", action="store_true")
    args = parser.parse_args()
    run(args)
