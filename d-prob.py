import argparse

from common import *

SymbolicCNFConstraintForSbox = SymbolicCNFConstraintForSbox55


def run(args):
    satsolver = solver_builder(args.solver)
    roundOrProb = InitialLowerBound
    tf = open(TIME, "a")
    tick("total")
    for round in range(SearchRoundStart, SearchRoundEnd):
        tick("round")
        matsuiRoundIndex, matsuiCount = matsui(round)
        while True:
            cnfbuilder_diff_prob(
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
        DifferentialProbabilityBound[round] = roundOrProb - 1
        tick("round")
        tf.write(f"Round: {round}; Active: {roundOrProb - 1}; Cost: {cost('round')}\n")
    tick("total")
    tf.write(f"Total Runtime: {cost('total')}\n\n")
    tf.close()
    log(DifferentialProbabilityBound)
    log(f"Total Runtime: {cost('total')}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--solver", type=str, required=True)
    parser.add_argument("--sbva", action="store_true")
    args = parser.parse_args()
    run(args)
